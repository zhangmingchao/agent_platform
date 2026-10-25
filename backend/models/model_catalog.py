"""百炼目录的上游解析实体和公开响应实体；公开实体不包含凭据。"""
from pydantic import BaseModel, Field, JsonValue


class CatalogModalities(BaseModel):
    """上游输入输出模态，用于判断是否支持文字聊天。"""

    request_modality: list[str] = Field(default_factory=list, description="可接受的输入模态")
    response_modality: list[str] = Field(default_factory=list, description="可生成的输出模态")


class CatalogModelInfo(BaseModel):
    """上游模型限制，用于展示上下文和输出长度提示。"""

    context_window: int | None = Field(default=None, description="上下文窗口 Token 数")
    max_output_tokens: int | None = Field(default=None, description="最大输出 Token 数")


class BailianUpstreamModel(BaseModel):
    """百炼单条模型记录；未知字段由 Pydantic 忽略。"""

    model: str = Field(min_length=1, description="调用时使用的模型 ID")
    name: str = Field(default="", description="模型展示名称")
    description: str = Field(default="", description="模型说明")
    capabilities: list[str] = Field(default_factory=list, description="TG 等能力标记")
    features: list[str] = Field(default_factory=list, description="工具调用等特性")
    inference_metadata: CatalogModalities = Field(default_factory=CatalogModalities, description="输入输出模态")
    model_info: CatalogModelInfo = Field(default_factory=CatalogModelInfo, description="Token 限制")
    inference_offline_info: JsonValue = Field(default=None, description="上游下线信息")

    def supports_text_chat(self) -> bool:
        """仅初筛文字生成、文字输入输出、非实时且没有下线信息的模型。"""
        return (
            "TG" in self.capabilities
            and "Text" in self.inference_metadata.request_modality
            and "Text" in self.inference_metadata.response_modality
            and "realtime" not in self.model.lower()
            and not self.inference_offline_info
        )


class BailianUpstreamPage(BaseModel):
    """上游分页数据，用于遍历完整目录。"""

    total: int = Field(ge=0, le=5000, description="上游全部模型数量，上限防止异常分页")
    models: list[BailianUpstreamModel] = Field(description="当前页模型记录")


class BailianUpstreamResponse(BaseModel):
    """上游业务响应；错误信息不直接透传，避免泄露凭据。"""

    success: bool = Field(description="上游业务请求是否成功")
    output: BailianUpstreamPage | None = Field(default=None, description="成功响应的分页实体")


class CatalogModel(BaseModel):
    """前端可选择的模型；所有字段均为公开模型信息。"""

    model_id: str = Field(description="推理模型 ID")
    name: str = Field(description="展示名称")
    description: str = Field(description="模型说明")
    provider: str = Field(default="qwen", description="平台 OpenAI 兼容适配器标识")
    base_url: str = Field(description="兼容 API 基础地址，不含 chat/completions")
    features: list[str] = Field(description="上游声明的特性")
    context_window: int | None = Field(description="上下文窗口 Token 数")
    max_output_tokens: int | None = Field(description="最大输出 Token 数")


class ModelCatalogPage(BaseModel):
    """经过文字聊天筛选和搜索后的分页响应。"""

    items: list[CatalogModel] = Field(description="当前页公开模型")
    total: int = Field(description="筛选并搜索后的总数")
    page_no: int = Field(description="当前页码，从 1 开始")
    page_size: int = Field(description="每页数量")
    source: str = Field(default="aliyun-bailian", description="目录来源")
