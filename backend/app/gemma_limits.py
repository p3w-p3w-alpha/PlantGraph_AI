"""Safe quota diagnostics for Gemma through the Gemini API.

Only quota identifiers, numeric limits and a bounded delay leave this module.
Provider messages, URLs, request/response headers, project dimensions and keys
are intentionally excluded. No network access or provider-specific retry occurs.
"""
from __future__ import annotations

import math
import re
from typing import Any

_METRIC = re.compile(r'[a-z][a-z0-9.]*\.googleapis\.com/[A-Za-z0-9_.-]{1,160}\Z')
_QUOTA_ID = re.compile(r'[A-Za-z][A-Za-z0-9_.-]{0,159}\Z')
_DAILY = re.compile(r'per[ _-]?day|daily|per[ _-]?24[ _-]?hours',re.IGNORECASE)
_SECRET_MARKERS = ('AIza','sk-ant-','sk-proj-','Bearer ')


def _safe_identifier(value: Any, metric: bool = False) -> str | None:
    if not isinstance(value,str) or any(marker in value for marker in _SECRET_MARKERS):
        return None
    return value if (_METRIC if metric else _QUOTA_ID).fullmatch(value) else None


def _number(value: Any) -> int | float | None:
    if isinstance(value,bool):return None
    try:number=float(value)
    except (ValueError,TypeError,OverflowError):return None
    if not math.isfinite(number) or number<0:return None
    return int(number) if number.is_integer() else number


def _retry_seconds(value: Any) -> int | None:
    if isinstance(value,str):
        match=re.fullmatch(r'\s*(\d+(?:\.\d+)?)s\s*',value)
        if not match:return None
        seconds=float(match.group(1))
    elif isinstance(value,dict):
        seconds=_number(value.get('seconds',0))
        nanos=_number(value.get('nanos',0))
        if seconds is None or nanos is None or nanos>=1_000_000_000:return None
        seconds+=nanos/1_000_000_000
    else:return None
    if not math.isfinite(seconds):return None
    return max(1,min(60,math.ceil(seconds)))


def parse_quota_error(error_or_details: Any) -> dict:
    """Parse structured QuotaFailure/RetryInfo details without exposing context.

    Intended for a provider HTTP429 handler. Unknown429 details remain retryable
    with a conservative60s recommendation. Daily quotas and explicit zero quota
    allowance are not treated as transient. The caller decides whether to retry
    and must bound total attempts; a delay is not a promise quota will recover.
    """
    payload=getattr(error_or_details,'details',error_or_details)
    metrics=[];ids=[];limits=[];delays=[];daily=False;zero=False
    pending=[payload];visited=0
    while pending and visited<1000:
        block=pending.pop();visited+=1
        if isinstance(block,list):pending.extend(block[:1000]);continue
        if not isinstance(block,dict):continue
        # Traverse the documented wrappers, never arbitrary provider dimensions.
        if isinstance(block.get('error'),(dict,list)):pending.append(block['error'])
        if isinstance(block.get('details'),(dict,list)):pending.append(block['details'])
        type_name=str(block.get('@type',''))
        if type_name.endswith('RetryInfo'):
            delay=_retry_seconds(block.get('retryDelay',block.get('retry_delay')))
            if delay is not None:delays.append(delay)
        if not type_name.endswith('QuotaFailure'):continue
        violations=block.get('violations',[])
        if not isinstance(violations,list):continue
        for violation in violations[:1000]:
            if not isinstance(violation,dict):continue
            metric=_safe_identifier(violation.get('quotaMetric'),metric=True)
            quota_id=_safe_identifier(violation.get('quotaId'))
            value=_number(violation.get('quotaValue'))
            if metric and metric not in metrics:metrics.append(metric)
            if quota_id and quota_id not in ids:ids.append(quota_id)
            if value is not None:
                if value not in limits:limits.append(value)
                zero=zero or value==0
            # Description is used only for classification and is never emitted.
            classification=' '.join(str(violation.get(k,'')) for k in ('quotaMetric','quotaId','description'))
            daily=daily or bool(_DAILY.search(classification))
    return dict(quota_metrics=sorted(metrics),quota_ids=sorted(ids),limits=sorted(limits),retry_after_s=max(delays,default=60),retryable=not(daily or zero))
