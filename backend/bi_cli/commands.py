"""BI CLI 参数解析和只读接口白名单。"""

from __future__ import annotations

import argparse
from typing import Any, List, Sequence, Tuple

from .errors import BiCliError, BiCliFailure
from .models import (
    BiApiRequest,
    BiCliExitCode,
    BiHttpMethod,
    compact_query_items,
)


class BiArgumentParser(argparse.ArgumentParser):
    """将 argparse 错误转换成可由 CLI 输出为 JSON 的异常。"""

    def error(self, message: str) -> None:
        """阻止 argparse 直接向标准错误打印非结构化文本。

        Args:
            message: argparse 生成的参数错误说明。

        Raises:
            BiCliError: 始终抛出结构化参数错误。
        """
        raise BiCliError(
            BiCliFailure(
                exit_code=BiCliExitCode.USAGE_ERROR,
                error_code="INVALID_ARGUMENTS",
                message=message,
            )
        )


def _positive_int(value: str) -> int:
    """解析必须大于零的整数命令参数。

    Args:
        value: argparse 接收的原始字符串。

    Returns:
        经过正数校验的整数。
    """
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("必须大于 0")
    return parsed


def _page_size(value: str) -> int:
    """解析并限制单次列表查询的数据量。

    Args:
        value: argparse 接收的分页大小字符串。

    Returns:
        不超过 200 的正整数分页大小。
    """
    parsed = _positive_int(value)
    if parsed > 200:
        raise argparse.ArgumentTypeError("不能大于 200")
    return parsed


def _required_product_key(value: str) -> str:
    """清洗必填产品标识，避免空字符串进入 BI 接口。

    Args:
        value: 用户或 Agent 传入的产品标识。

    Returns:
        去除首尾空格后的产品标识。
    """
    normalized = value.strip()
    if not normalized:
        raise argparse.ArgumentTypeError("product-key 不能为空")
    if len(normalized) > 200:
        raise argparse.ArgumentTypeError("product-key 长度不能超过 200")
    return normalized


def _add_product_key(parser: argparse.ArgumentParser) -> None:
    """为列表命令添加统一的产品标识参数。

    Args:
        parser: 需要注册 ``--product-key`` 参数的子命令解析器。
    """
    parser.add_argument(
        "--product-key",
        required=True,
        type=_required_product_key,
        help="需要查询的 BI 产品标识",
    )


def _add_pagination(parser: argparse.ArgumentParser) -> None:
    """为分页列表命令添加统一的页码参数。

    Args:
        parser: 需要注册分页参数的子命令解析器。
    """
    parser.add_argument("--page-num", type=_positive_int, default=1, help="页码，从 1 开始")
    parser.add_argument("--page-size", type=_page_size, default=50, help="每页条数，最大 200")


def _build_parser() -> BiArgumentParser:
    """创建第一期只读 BI 元数据命令树。"""
    parser = BiArgumentParser(prog="bi", description="Agent 原生 BI 元数据 CLI")
    root_subparsers = parser.add_subparsers(dest="group", required=True)
    metadata_parser = root_subparsers.add_parser("metadata", help="查询 BI 元数据")
    domain_subparsers = metadata_parser.add_subparsers(dest="domain", required=True)

    analysis_body_parser = domain_subparsers.add_parser(
        "analysis-bodies", help="分析主体元数据",
    )
    analysis_body_action = analysis_body_parser.add_subparsers(dest="action", required=True)
    analysis_body_list = analysis_body_action.add_parser("list", help="查询分析主体列表")
    _add_product_key(analysis_body_list)

    event_parser = domain_subparsers.add_parser("events", help="事件元数据")
    event_action = event_parser.add_subparsers(dest="action", required=True)
    event_list = event_action.add_parser("list", help="查询事件列表")
    _add_product_key(event_list)
    _add_pagination(event_list)
    event_list.add_argument("--search-text", help="按事件名称或标识搜索")
    event_list.add_argument(
        "--event-classify",
        type=int,
        action="append",
        help="事件分类，可重复传入",
    )

    user_profile_parser = domain_subparsers.add_parser(
        "user-properties", help="用户属性元数据",
    )
    user_profile_action = user_profile_parser.add_subparsers(dest="action", required=True)
    user_profile_list = user_profile_action.add_parser("list", help="查询全量用户属性")
    _add_product_key(user_profile_list)
    user_profile_list.add_argument(
        "--profile-classify-list",
        help="用户属性分类编号，多个编号使用英文逗号分隔",
    )
    user_profile_list.add_argument("--table-type", type=int, help="分析主体表类型")
    user_profile_list.add_argument(
        "--entity-type",
        default="users",
        help="分析主体字段，默认 users",
    )

    event_profile_parser = domain_subparsers.add_parser(
        "event-properties", help="事件属性元数据",
    )
    event_profile_action = event_profile_parser.add_subparsers(dest="action", required=True)
    event_profile_list = event_profile_action.add_parser("list", help="查询事件属性列表")
    _add_product_key(event_profile_list)
    _add_pagination(event_profile_list)
    event_profile_list.add_argument("--search-text", help="按属性名称或标识搜索")
    event_profile_list.add_argument(
        "--profile-classify",
        type=int,
        action="append",
        help="属性分类，可重复传入",
    )
    event_profile_list.add_argument(
        "--profile-type",
        type=int,
        action="append",
        help="属性数据类型，可重复传入",
    )

    metric_parser = domain_subparsers.add_parser("metrics", help="事件指标元数据")
    metric_action = metric_parser.add_subparsers(dest="action", required=True)
    metric_list = metric_action.add_parser("list", help="查询事件指标列表")
    _add_product_key(metric_list)
    _add_pagination(metric_list)
    metric_list.add_argument("--category", type=int, help="指标分类")
    metric_list.add_argument("--search-text", help="按指标名称搜索")
    metric_list.add_argument("--sort-field-name", help="排序字段")
    metric_list.add_argument("--sort-type", type=int, help="排序方式")
    return parser


def _event_classify_items(values: Sequence[int] | None) -> List[Tuple[str, Any]]:
    """将事件分类数组转换为 Spring MVC 可识别的重复查询参数。

    Args:
        values: 一个或多个事件分类编号；为空时不增加筛选参数。

    Returns:
        参数名固定为 ``eventClassifyArr`` 的键值对列表。
    """
    return [("eventClassifyArr", value) for value in values or []]


def parse_bi_cli_command(arguments: Sequence[str]) -> BiApiRequest:
    """将 CLI 参数转换为白名单内的强类型 HTTP 请求。

    Args:
        arguments: 不包含可执行文件名的 CLI 参数列表。

    Returns:
        只可能指向第一期五个只读接口之一的请求实体。

    Raises:
        BiCliError: 命令、参数或取值不符合白名单约束。
    """
    namespace = _build_parser().parse_args(list(arguments))
    product_key = str(namespace.product_key)

    if namespace.domain == "analysis-bodies":
        return BiApiRequest(
            command_name="metadata.analysis-bodies.list",
            method=BiHttpMethod.GET,
            path="/analysisBody/bodyList",
            product_key=product_key,
            query_items=(("productKey", product_key),),
        )

    if namespace.domain == "events":
        query_items: List[Tuple[str, Any]] = [
            ("productKey", product_key),
            ("pageNum", namespace.page_num),
            ("pageSize", namespace.page_size),
            ("searchText", namespace.search_text),
        ]
        query_items.extend(_event_classify_items(namespace.event_classify))
        return BiApiRequest(
            command_name="metadata.events.list",
            method=BiHttpMethod.GET,
            path="/eventConfig/findByProductKey",
            product_key=product_key,
            query_items=compact_query_items(query_items),
        )

    if namespace.domain == "user-properties":
        return BiApiRequest(
            command_name="metadata.user-properties.list",
            method=BiHttpMethod.GET,
            path="/profileUser/findAllUserProfList",
            product_key=product_key,
            query_items=compact_query_items(
                (
                    ("productKey", product_key),
                    ("profileClassifyList", namespace.profile_classify_list),
                    ("tableType", namespace.table_type),
                    ("entityType", namespace.entity_type),
                )
            ),
        )

    if namespace.domain == "event-properties":
        body = {
            "productKey": product_key,
            "searchText": namespace.search_text,
            "profileClassifyList": namespace.profile_classify,
            "profileTypeList": namespace.profile_type,
        }
        return BiApiRequest(
            command_name="metadata.event-properties.list",
            method=BiHttpMethod.POST,
            path="/profileType/findByProductKey",
            product_key=product_key,
            query_items=(("pageNum", namespace.page_num), ("pageSize", namespace.page_size)),
            json_body={key: value for key, value in body.items() if value is not None},
        )

    if namespace.domain == "metrics":
        return BiApiRequest(
            command_name="metadata.metrics.list",
            method=BiHttpMethod.GET,
            path="/eventMetric/metricList",
            product_key=product_key,
            query_items=compact_query_items(
                (
                    ("productKey", product_key),
                    ("pageNum", namespace.page_num),
                    ("pageSize", namespace.page_size),
                    ("category", namespace.category),
                    ("searchText", namespace.search_text),
                    ("sortFieldName", namespace.sort_field_name),
                    ("sortType", namespace.sort_type),
                )
            ),
        )

    raise BiCliError(
        BiCliFailure(
            exit_code=BiCliExitCode.USAGE_ERROR,
            error_code="UNSUPPORTED_COMMAND",
            message="当前 BI CLI 命令不在第一期只读白名单中",
        )
    )
