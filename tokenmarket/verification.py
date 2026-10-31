"""Verification & settlement interfaces (stubs for v1).

TODO(B1): real model-identity verification (TEE remote attestation, output watermark / fingerprint
detection, statistical probing) and token-count verification. In v1 every check returns
'unverified' and settlement trusts the seller-reported token count.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

UNVERIFIED = "unverified"


@dataclass
class Settlement:
    buyer_pays: float      # price * tokens (excl. gateway fee)
    seller_receives: float
    fee: float
    status: str


class VerificationModule(ABC):
    @abstractmethod
    def verify_model_identity(self, tx: Dict) -> str:
        """Return 'verified' | 'mismatch' | 'unverified' for the claimed model."""

    @abstractmethod
    def verify_token_count(self, tx: Dict) -> str:
        """Return 'verified' | 'mismatch' | 'unverified' for the reported reasoning-token count."""

    @abstractmethod
    def settle(self, tx: Dict) -> Settlement:
        """Compute payments for an allowed transaction."""


class TrustingVerifier(VerificationModule):
    """Default v1 verifier: trusts seller claims; cannot detect model swaps."""

    def verify_model_identity(self, tx: Dict) -> str:
        return UNVERIFIED

    def verify_token_count(self, tx: Dict) -> str:
        return UNVERIFIED

    def settle(self, tx: Dict) -> Settlement:
        # v4: the buyer pays for BILLED tokens (== reasoning_tokens unless the seller commits token theft)
        gross = tx["price_per_1k"] * tx.get("billed_tokens", tx["reasoning_tokens"]) / 1000.0
        fee = gross * tx.get("fee_rate", 0.0)
        return Settlement(buyer_pays=gross, seller_receives=gross, fee=fee, status=UNVERIFIED)


class TEEAttestationVerifier(TrustingVerifier):
    """TODO(B1): verify a TEE (e.g. SGX/TDX/SEV-SNP, GPU CC) attestation quote binding the model hash."""

    def verify_model_identity(self, tx: Dict) -> str:
        raise NotImplementedError("TEE attestation verification is a B1 TODO")


class WatermarkVerifier(TrustingVerifier):
    """TODO(B1): detect model-specific watermark / fingerprint in reasoning output."""

    def verify_model_identity(self, tx: Dict) -> str:
        return UNVERIFIED  # TODO(B1): implement watermark detection


VERIFIERS = {"trusting": TrustingVerifier, "tee": TEEAttestationVerifier, "watermark": WatermarkVerifier}
