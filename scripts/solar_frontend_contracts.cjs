/**
 * 用 TypeScript AST 和类型检查器提取 SolarEngine 前端接口，不执行前端业务代码。
 * 参数：argv[2] 为 solar-engine-fe 根目录；argv[3] 为生成的 JSON 文件。
 * 输出：URL 常量、HTTP 调用、参数/返回 Schema 以及源码位置；未知类型明确标记。
 */
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(process.argv[2]);
const ts = require(path.join(root, 'node_modules/typescript'));
const output = process.argv[3];

/** 遍历 dir 下后缀为 .ts 的源码；dir 为 API 源码目录。 */
function files(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const full = path.join(dir, entry.name);
    return entry.isDirectory() ? files(full) : full.endsWith('.ts') ? [full] : [];
  });
}
const configPath = path.join(root, 'tsconfig.json');
const config = ts.readConfigFile(configPath, ts.sys.readFile).config;
const parsed = ts.parseJsonConfigFileContent(config, ts.sys, root);
const sources = files(path.join(root, 'src/api'));
const program = ts.createProgram(sources, { ...parsed.options, noEmit: true });
const checker = program.getTypeChecker();

/** 返回 node 的项目相对位置；node 为 AST 节点。 */
function location(node) {
  const source = node.getSourceFile();
  return { file: path.relative(root, source.fileName).replaceAll('\\', '/'), line: source.getLineAndCharacterOfPosition(node.getStart()).line + 1 };
}

/** 从 node 的前导注释读取业务描述；不执行注释中的指令。 */
function description(node) {
  const source = node.getSourceFile();
  const ranges = ts.getLeadingCommentRanges(source.text, node.pos) || [];
  return ranges.map(range => source.text.slice(range.pos, range.end).replace(/\/\*\*?|\*\/|\/\/|^\s*\*/gm, '').trim()).filter(Boolean).join(' ');
}

/** 将 type 转为 JSON Schema；seen 防止递归循环，depth 限制展开深度，未知处保留原类型。 */
function schema(type, seen = new Set(), depth = 0) {
  const label = checker.typeToString(type);
  if (type.flags & (ts.TypeFlags.Any | ts.TypeFlags.Unknown | ts.TypeFlags.TypeParameter)) return { 'x-unresolved': label };
  if (type.flags & ts.TypeFlags.StringLiteral) return { type: 'string', const: type.value };
  if (type.flags & ts.TypeFlags.NumberLiteral) return { type: 'number', const: type.value };
  if (type.flags & ts.TypeFlags.BooleanLiteral) return { type: 'boolean', const: type.intrinsicName === 'true' };
  if (type.flags & ts.TypeFlags.StringLike) return { type: 'string' };
  if (type.flags & ts.TypeFlags.NumberLike) return { type: 'number' };
  if (type.flags & ts.TypeFlags.BooleanLike) return { type: 'boolean' };
  if (type.flags & ts.TypeFlags.Null) return { type: 'null' };
  if (type.isUnion()) {
    const members = type.types.filter(t => !(t.flags & ts.TypeFlags.Undefined)).map(t => schema(t, seen, depth));
    return members.length === 1 ? members[0] : { anyOf: members };
  }
  if (seen.has(type) || depth >= 7) return { 'x-unresolved': label, 'x-reason': '递归或超过七层，需查看源码类型' };
  const next = new Set(seen).add(type);
  if (checker.isArrayType(type) || checker.isTupleType(type)) {
    const args = checker.getTypeArguments(type);
    return { type: 'array', items: args.length ? schema(args[0], next, depth + 1) : {} };
  }
  if (type.flags & ts.TypeFlags.Object || type.isIntersection()) {
    const properties = {};
    const required = [];
    for (const symbol of checker.getPropertiesOfType(type)) {
      const decl = symbol.valueDeclaration || symbol.declarations?.[0];
      if (!decl || checker.getSignaturesOfType(checker.getTypeOfSymbolAtLocation(symbol, decl), ts.SignatureKind.Call).length) continue;
      const value = schema(checker.getTypeOfSymbolAtLocation(symbol, decl), next, depth + 1);
      const doc = ts.displayPartsToString(symbol.getDocumentationComment(checker));
      properties[symbol.name] = doc ? { ...value, description: doc } : value;
      if (!(symbol.flags & ts.SymbolFlags.Optional)) required.push(symbol.name);
    }
    const index = checker.getIndexTypeOfType(type, ts.IndexKind.String);
    if (!Object.keys(properties).length && !index) return { 'x-unresolved': label };
    return { type: 'object', properties, ...(required.length ? { required } : {}), ...(index ? { additionalProperties: schema(index, next, depth + 1) } : {}) };
  }
  return { 'x-unresolved': label };
}

const urls = new Map();
const aliases = new Map();
const index = program.getSourceFile(path.join(root, 'src/api/url/index.ts'));
for (const statement of index.statements) {
  if (ts.isImportDeclaration(statement) && statement.importClause?.name && ts.isStringLiteral(statement.moduleSpecifier)) {
    aliases.set(statement.importClause.name.text, path.resolve(path.dirname(index.fileName), statement.moduleSpecifier.text + '.ts'));
  }
}

/** 提取 value 对象中的 URL 常量；prefix 是 URL 常量引用前缀。 */
function walkObject(value, prefix) {
  if (!ts.isObjectLiteralExpression(value)) return;
  for (const prop of value.properties) {
    if (!ts.isPropertyAssignment(prop)) continue;
    const name = prop.name.getText().replace(/^['"]|['"]$/g, '');
    const key = [...prefix, name].join('.');
    if (ts.isObjectLiteralExpression(prop.initializer)) walkObject(prop.initializer, [...prefix, name]);
    else if (ts.isStringLiteral(prop.initializer) || ts.isNoSubstitutionTemplateLiteral(prop.initializer)) {
      urls.set(key, { reference: key, path: prop.initializer.text, description: description(prop), source: location(prop) });
    }
  }
}
for (const [alias, file] of aliases) {
  const source = program.getSourceFile(file);
  if (!source) continue;
  for (const statement of source.statements) if (ts.isExportAssignment(statement)) walkObject(statement.expression, ['URL', alias]);
}

const calls = [];
const unresolvedCalls = [];
/** 记录 node 的接口契约；method 为 HTTP 方法，url/parameter 为真实调用参数节点，body 可区分混合传参。 */
function record(node, method, url, parameter, body, wireMode = 'default') {
  const reference = url?.getText();
  const contract = urls.get(reference);
  const literal = url && ts.isStringLiteral(url) ? url.text : null;
  if (!contract && !literal) {
    if (reference) unresolvedCalls.push({ method, expression: reference, source: location(node) });
    return;
  }
  let parent = node.parent;
  while (parent && !ts.isMethodDeclaration(parent) && !ts.isPropertyAssignment(parent) && !ts.isFunctionDeclaration(parent)) parent = parent.parent;
  const inputSchema = parameter ? schema(checker.getTypeAtLocation(parameter)) : { type: 'object', properties: {} };
  calls.push({ ...(contract || { path: literal, reference: literal }), method, source: location(node), function: parent?.name?.getText() || '', description: parent ? description(parent) : '', input_schema: inputSchema, input_type: parameter ? checker.typeToString(checker.getTypeAtLocation(parameter)) : 'none', wire_mode: wireMode, ...(wireMode === 'query_body' ? { frontend_query_schema: inputSchema, frontend_body_schema: body ? schema(checker.getTypeAtLocation(body)) : null } : {}), response_schema: node.typeArguments?.[0] ? schema(checker.getTypeFromTypeNode(node.typeArguments[0])) : { 'x-unresolved': '未声明前端返回泛型' } });
}
/** 搜索 node 子树中的 Http 调用；调用 URL 必须来自 AST 可解析的常量或字符串。 */
function visit(node) {
  if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && ['httpGet', 'httpPost'].includes(node.expression.text)) {
    record(node, node.expression.text === 'httpGet' ? 'GET' : 'POST', node.arguments[0], node.arguments[1]);
  }
  if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression)) {
    const originalMethod = node.expression.name.text.toUpperCase();
    const method = ['POSTANDGET', 'DOWNLOAD'].includes(originalMethod) ? 'POST' : originalMethod;
    const owner = node.expression.expression.getText();
    if (owner === 'Http' && ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
      record(node, method, node.arguments[0], node.arguments[1], node.arguments[2], originalMethod === 'POSTANDGET' ? 'query_body' : originalMethod === 'DOWNLOAD' ? 'binary' : ['PUT', 'PATCH', 'DELETE'].includes(method) ? 'query' : 'default');
    } else if (owner === 'RequestCache' && node.expression.name.text === 'request' && ts.isPropertyAccessExpression(node.arguments[0]) && node.arguments[0].expression.getText() === 'Http' && ts.isArrayLiteralExpression(node.arguments[1])) {
      const args = node.arguments[1].elements;
      record(node, node.arguments[0].name.text.toUpperCase(), args[0], args[1]);
    } else if (owner === 'RequestCache' && node.expression.name.text === 'request' && ts.isIdentifier(node.arguments[0]) && ['httpGet', 'httpPost'].includes(node.arguments[0].text)) {
      record(node, node.arguments[0].text === 'httpGet' ? 'GET' : 'POST', node.arguments[1], node.arguments[2]);
    }
  }
  ts.forEachChild(node, visit);
}
for (const source of program.getSourceFiles()) {
  if (source.fileName.startsWith(path.join(root, 'src/api/modules'))) visit(source);
}
fs.writeFileSync(output, JSON.stringify({ urls: [...urls.values()], calls, unresolved_calls: unresolvedCalls }, null, 2) + '\n');
console.log(JSON.stringify({ urls: urls.size, calls: calls.length, unresolved_calls: unresolvedCalls.length }));
