# Generated from contract/openapi.json; do not edit.
from typing import Any, Literal, NotRequired, TypedDict

class CreateVerificationRequestBody(TypedDict):
    name: str
    purpose: str
    credential_type: str
    policy_profile: str
    expires_at: NotRequired[str | None]
    callback_mode: NotRequired[str]
    redirect_uri: str
    registration_certificate_id: NotRequired[str | None]
    requested_claims: list[list[Any]]
    rp_service_id: NotRequired[str | None]
    rp_instance_id: NotRequired[str | None]

class VerificationRequestResponse(TypedDict):
    id: str
    name: str
    purpose: str
    credential_type: str
    policy_profile: str
    expires_at: str | None
    callback_mode: str
    active: bool
    published_assets: dict[str, Any]
    intended_use_identifier: NotRequired[str | None]
    requested_claims: NotRequired[list[list[Any]] | None]
    rp_service_id: NotRequired[str | None]
    rp_instance_id: NotRequired[str | None]

class VerificationSessionResponse(TypedDict):
    session_id: str
    authorization_request_url: str
    request_uri: NotRequired[str | None]
    state: NotRequired[str | None]
    nonce: NotRequired[str | None]
    expires_at: str
    transaction_id: NotRequired[str | None]
    mode: NotRequired[str]
    simulated: NotRequired[bool]
    billable: NotRequired[bool | None]
    branded_verification_page: NotRequired[bool]
    branded_qr_code: NotRequired[bool]

class SessionStatusResponse(TypedDict):
    status: str
    session_id: str
    created_at: NotRequired[str | None]
    expires_at: NotRequired[str | None]
    submission_id: NotRequired[str | None]
    accepted: NotRequired[bool | None]
    failure_reason: NotRequired[str | None]
    verified_claims: NotRequired[dict[str, Any] | None]
    mode: NotRequired[str]
    simulated: NotRequired[bool]
    billable: NotRequired[bool | None]
    claims: NotRequired[dict[str, Any] | None]
    verification_status: NotRequired[str | None]
    trust_status: NotRequired[str | None]

class Error(TypedDict):
    detail: NotRequired[Any]

class CampaignBody(TypedDict):
    name: str
    purpose: str
    profile: NotRequired[Literal['pid', 'mdl']]

class Campaign(TypedDict):
    id: str
    name: str
    purpose: str
    profile: Literal['pid', 'mdl']
    mode: Literal['simulator']
    simulated: Literal[True]

class TokenBody(TypedDict):
    token: str

class OutcomeBody(TypedDict):
    token: str
    scenario: Literal['approved', 'consent_rejected', 'missing_attributes', 'ineligible', 'timeout']

class SimulatorInspect(TypedDict):
    status: Literal['pending', 'completed', 'failed', 'expired']
    session_id: str
    created_at: NotRequired[str | None]
    expires_at: NotRequired[str | None]
    submission_id: NotRequired[str | None]
    accepted: NotRequired[bool | None]
    failure_reason: NotRequired[str | None]
    verified_claims: NotRequired[None]
    mode: Literal['simulator']
    simulated: Literal[True]
    billable: Literal[False]
    claims: NotRequired[dict[str, Any] | None]
    verification_status: NotRequired[Literal['simulated_pending', 'simulated_approved', 'simulated_failed']]
    trust_status: NotRequired[Literal['not_evaluated']]
    campaign: Campaign
    preview_claims: dict[str, Any]

class SimulatorResult(TypedDict):
    status: Literal['pending', 'completed', 'failed', 'expired']
    session_id: str
    created_at: NotRequired[str | None]
    expires_at: NotRequired[str | None]
    submission_id: NotRequired[str | None]
    accepted: NotRequired[bool | None]
    failure_reason: NotRequired[str | None]
    verified_claims: NotRequired[None]
    mode: Literal['simulator']
    simulated: Literal[True]
    billable: Literal[False]
    claims: NotRequired[dict[str, Any] | None]
    verification_status: NotRequired[Literal['simulated_pending', 'simulated_approved', 'simulated_failed']]
    trust_status: NotRequired[Literal['not_evaluated']]
