from types import SimpleNamespace
import json
import pytest

from app.gemma_limits import parse_quota_error


def error_payload(quota_id='GenerateContentInputTokensPerModelPerMinute-FreeTier',value='15000',delay='12.4s'):
    return {'error':{'code':429,'message':'Do not log this provider message or request URL','details':[
        {'@type':'type.googleapis.com/google.rpc.QuotaFailure','violations':[{'quotaMetric':'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count','quotaId':quota_id,'quotaValue':value,'quotaDimensions':{'model':'gemma-4-26b-a4b-it','project':'PRIVATE-PROJECT-123','key':'AIzaNEVER-EXPOSE'}}]},
        {'@type':'type.googleapis.com/google.rpc.RetryInfo','retryDelay':delay},
    ]}}


def test_nested_sdk_error_extracts_safe_minute_limit_and_delay():
    result=parse_quota_error(SimpleNamespace(details=error_payload()))
    assert result=={'quota_metrics':['generativelanguage.googleapis.com/generate_content_free_tier_input_token_count'],'quota_ids':['GenerateContentInputTokensPerModelPerMinute-FreeTier'],'limits':[15000],'retry_after_s':13,'retryable':True}
    raw=json.dumps(result)
    for forbidden in ['PRIVATE-PROJECT','AIza','provider message','quotaDimensions','headers','key']:
        assert forbidden not in raw


@pytest.mark.parametrize('quota_id',['GenerateRequestsPerDayPerProjectPerModel-FreeTier','input_tokens_per_day','DailyModelTokens'])
def test_daily_quota_is_not_retried_even_with_retry_info(quota_id):
    result=parse_quota_error(error_payload(quota_id=quota_id,delay='1s'))
    assert not result['retryable']


def test_zero_allowance_is_not_retried():
    result=parse_quota_error(error_payload(value='0'))
    assert result['limits']==[0]
    assert not result['retryable']


@pytest.mark.parametrize('delay,expected',[('0s',1),('0.01s',1),('60s',60),('120s',60),('-1s',60),('broken',60),({'seconds':'4','nanos':1},5),({'seconds':'2','nanos':500_000_000},3)])
def test_delays_are_bounded_and_malformed_values_use_default(delay,expected):
    assert parse_quota_error(error_payload(delay=delay))['retry_after_s']==expected


@pytest.mark.parametrize('payload',[None,{},[],{'error':{'message':'private'}},{'details':'unexpected'}])
def test_unknown_429_has_safe_conservative_default(payload):
    assert parse_quota_error(payload)=={'quota_metrics':[],'quota_ids':[],'limits':[],'retry_after_s':60,'retryable':True}


def test_unsafe_identifiers_and_nonfinite_values_are_not_returned():
    payload=error_payload(quota_id='projects/SECRET?key=AIzaSECRET',value='NaN')
    payload['error']['details'][0]['violations'][0]['quotaMetric']='https://example.com?key=AIzaSECRET'
    result=parse_quota_error(payload)
    assert not result['quota_ids'] and not result['quota_metrics'] and not result['limits']
    assert 'SECRET' not in json.dumps(result)


def test_multiple_violations_are_deduplicated_and_daily_overrides_minute():
    first=error_payload();daily=error_payload(quota_id='GenerateRequestsPerDay',value=1000)
    first['error']['details'].extend(daily['error']['details'])
    first['error']['details'].append(first['error']['details'][0])
    result=parse_quota_error(first)
    assert len(result['quota_metrics'])==1
    assert result['limits']==[1000,15000]
    assert not result['retryable']
