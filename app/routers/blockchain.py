from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import os
import uuid

from app.database import get_db
from app.utils.dependencies import get_current_user

from app.models.blockchain import BlockchainTransaction
from app.models.contract import Contract

from app.services.blockchain_utils import (
    hash_contract,
    generate_tx_hash,
    generate_block_number,
    extract_text_from_pdf,
    extract_text_from_docx
)

router = APIRouter(prefix="/blockchain", tags=["Blockchain"])


# ======================================================
# 1) EMBED CONTRACT
# ======================================================
@router.post("/embed")
async def embed_contract(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    contract_id = payload.get("contract_id")
    signers = payload.get("signers", [])

    if not contract_id:
        raise HTTPException(status_code=400, detail="contract_id is required")

    # دریافت قرارداد از دیتابیس
    stmt = select(Contract).where(Contract.id == contract_id)
    result = await db.execute(stmt)
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # جلوگیری از دسترسی به قرارداد دیگران
    if contract.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    text = contract.content

    if not text:
        raise HTTPException(status_code=400, detail="Contract content is empty")

    contract_hash = hash_contract(text)
    tx_hash = generate_tx_hash()
    block_number = generate_block_number()

    tx = BlockchainTransaction(
        tx_hash=tx_hash,
        contract_id=contract_id,
        contract_hash=contract_hash,
        block_number=block_number,
        status="success",
        type="embed",
        signers=signers,
        timestamp=datetime.utcnow()
    )

    db.add(tx)
    await db.commit()
    await db.refresh(tx)

    return {
        "tx_hash": tx_hash,
        "contract_hash": contract_hash,
        "status": "success",
        "block_number": block_number,
        "timestamp": tx.timestamp,
        "signers": signers
    }


# ======================================================
# 2) VERIFY CONTRACT FILE
# ======================================================
@router.post("/verify/file")
async def verify_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    ext = file.filename.split(".")[-1].lower()
    temp_path = f"/tmp/{uuid.uuid4()}.{ext}"

    try:

        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # استخراج متن
        if ext == "pdf":
            text = extract_text_from_pdf(temp_path)

        elif ext == "docx":
            text = extract_text_from_docx(temp_path)

        else:
            raise HTTPException(
                status_code=400,
                detail="Allowed file types: PDF, DOCX"
            )

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text")

    contract_hash = hash_contract(text)

    stmt = select(BlockchainTransaction).where(
        BlockchainTransaction.contract_hash == contract_hash
    )

    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if record:
        return {
            "matched": True,
            "tampered": False,
            "contract_hash": contract_hash,
            "original_hash": contract_hash,
            "block_number": record.block_number,
            "timestamp": record.timestamp
        }

    return {
        "matched": False,
        "tampered": True,
        "contract_hash": contract_hash,
        "original_hash": None
    }


# ======================================================
# 3) VERIFY HASH
# ======================================================
@router.post("/verify/hash")
async def verify_hash(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    contract_hash = payload.get("contract_hash")

    if not contract_hash:
        raise HTTPException(
            status_code=400,
            detail="contract_hash is required"
        )

    stmt = select(BlockchainTransaction).where(
        BlockchainTransaction.contract_hash == contract_hash
    )

    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if record:
        return {
            "exists": True,
            "block_number": record.block_number,
            "timestamp": record.timestamp
        }

    return {"exists": False}


# ======================================================
# 4) HISTORY
# ======================================================
@router.get("/history")
async def history(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    stmt = select(BlockchainTransaction).order_by(
        BlockchainTransaction.timestamp.desc()
    )

    result = await db.execute(stmt)
    records = result.scalars().all()

    return [
        {
            "tx_hash": r.tx_hash,
            "contract_hash": r.contract_hash,
            "contract_id": r.contract_id,
            "type": r.type,
            "status": r.status,
            "block_number": r.block_number,
            "timestamp": r.timestamp,
            "signers": r.signers
        }
        for r in records
    ]


# ======================================================
# 5) STATS
# ======================================================
@router.get("/stats")
async def stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    stmt = select(BlockchainTransaction)
    result = await db.execute(stmt)
    all_tx = result.scalars().all()

    total_embedded = len([t for t in all_tx if t.type == "embed"])
    total_verified = len([t for t in all_tx if t.type.startswith("verify")])
    failed = len([t for t in all_tx if t.status == "failed"])

    return {
        "total_embedded": total_embedded,
        "total_verified": total_verified,
        "failed": failed,
        "avg_confirmation": "2.3s"
    }
