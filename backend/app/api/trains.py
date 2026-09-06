"""
Train Schedule & Corridor API
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from app.core.auth import get_current_user
from app.core.database import get_db

router = APIRouter()


@router.get("")
async def get_trains(
    corridor_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    train_type: Optional[str] = Query(None),
    is_goods: Optional[bool] = Query(None),
    limit: int = Query(200, le=500),
    current_user: dict = Depends(get_current_user),
):
    """Get train schedule from simulated COA data"""
    try:
        db = get_db()
        query = db.table("train_schedule").select("*")
        if corridor_id:
            query = query.eq("corridor_id", corridor_id)
        if date:
            query = query.eq("date", date)
        if train_type:
            query = query.eq("train_type", train_type)
        if is_goods is not None:
            query = query.eq("is_goods_train", is_goods)

        result = query.order("departure_time").limit(limit).execute()
        return {
            "trains": result.data or [],
            "total": len(result.data or []),
            "data_note": "SIMULATED_COA_DATA",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corridors")
async def get_corridors(current_user: dict = Depends(get_current_user)):
    """Get all railway corridors"""
    try:
        db = get_db()
        result = db.table("corridors").select("*").execute()
        return {"corridors": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/block-windows")
async def get_block_windows(
    corridor_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    available_only: bool = Query(True),
    current_user: dict = Depends(get_current_user),
):
    """Get available maintenance block windows"""
    try:
        db = get_db()
        query = db.table("block_windows").select("*")
        if corridor_id:
            query = query.eq("corridor_id", corridor_id)
        if date:
            query = query.eq("date", date)
        if available_only:
            query = query.eq("available", True)

        result = query.order("date").order("start_time").execute()
        return {"windows": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goods-forecast")
async def get_goods_forecast(
    corridor_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get goods train forecasts"""
    try:
        db = get_db()
        query = db.table("goods_forecast").select("*")
        if corridor_id:
            query = query.eq("corridor_id", corridor_id)
        result = query.execute()
        return {"forecasts": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
