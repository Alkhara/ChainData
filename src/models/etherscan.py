"""Etherscan models for ChainData."""

from typing import Optional
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """Ethereum transaction model."""
    
    blockNumber: str = Field(..., description="Block number")
    timeStamp: str = Field(..., description="Transaction timestamp")
    hash: str = Field(..., description="Transaction hash")
    nonce: str = Field(..., description="Transaction nonce")
    blockHash: str = Field(..., description="Block hash")
    transactionIndex: str = Field(..., description="Transaction index in block")
    from_address: str = Field(..., alias="from", description="Sender address")
    to_address: str = Field(..., alias="to", description="Recipient address")
    value: str = Field(..., description="Transaction value in wei")
    gas: str = Field(..., description="Gas limit")
    gasPrice: str = Field(..., description="Gas price in wei")
    gasUsed: str = Field(..., description="Gas used")
    cumulativeGasUsed: str = Field(..., description="Cumulative gas used")
    input: str = Field(..., description="Input data")
    contractAddress: Optional[str] = Field(None, description="Contract address if contract creation")
    confirmations: str = Field(..., description="Number of confirmations")
    isError: str = Field(..., description="Error status")
    txreceipt_status: str = Field(..., description="Transaction receipt status")


class TokenTransfer(BaseModel):
    """Ethereum token transfer model."""
    
    blockNumber: str = Field(..., description="Block number")
    timeStamp: str = Field(..., description="Transfer timestamp")
    hash: str = Field(..., description="Transaction hash")
    nonce: str = Field(..., description="Transaction nonce")
    blockHash: str = Field(..., description="Block hash")
    from_address: str = Field(..., alias="from", description="Sender address")
    contractAddress: str = Field(..., description="Token contract address")
    to_address: str = Field(..., alias="to", description="Recipient address")
    value: str = Field(..., description="Token value")
    tokenName: str = Field(..., description="Token name")
    tokenSymbol: str = Field(..., description="Token symbol")
    tokenDecimal: str = Field(..., description="Token decimals")
    transactionIndex: str = Field(..., description="Transaction index in block")
    gas: str = Field(..., description="Gas limit")
    gasPrice: str = Field(..., description="Gas price in wei")
    gasUsed: str = Field(..., description="Gas used")
    cumulativeGasUsed: str = Field(..., description="Cumulative gas used")
    input: str = Field(..., description="Input data")
    confirmations: str = Field(..., description="Number of confirmations")


class ContractSource(BaseModel):
    """Ethereum contract source code model."""
    
    SourceCode: str = Field(..., description="Contract source code")
    ABI: str = Field(..., description="Contract ABI")
    ContractName: str = Field(..., description="Contract name")
    CompilerVersion: str = Field(..., description="Compiler version")
    OptimizationUsed: str = Field(..., description="Optimization used")
    Runs: str = Field(..., description="Optimization runs")
    ConstructorArguments: str = Field(..., description="Constructor arguments")
    Library: str = Field(..., description="Library")
    LicenseType: str = Field(..., description="License type")
    Proxy: str = Field(..., description="Proxy status")
    Implementation: str = Field(..., description="Implementation address")
    SwarmSource: str = Field(..., description="Swarm source") 