from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Account, Rating
from ..schemas import RatingCreate, RatingOut, RatingStats
from ..deps import get_current_account, require_role

router = APIRouter(prefix="/feedback", tags=["feedback"])
_only_org_admin = require_role("org_admin", "super_admin")


@router.post("", response_model=RatingOut)
def submit_rating(payload: RatingCreate, db: Session = Depends(get_db), account: Account = Depends(get_current_account)):
    if not (1 <= payload.score <= 5):
        raise HTTPException(400, "التقييم يجب أن يكون بين 1 و 5")

    rating = Rating(
        account_id=account.id,
        organization_id=account.organization_id,
        turn_id=payload.turn_id,
        score=payload.score,
        comment=payload.comment,
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


@router.get("", response_model=list[RatingOut])
def list_ratings(db: Session = Depends(get_db), admin: Account = Depends(_only_org_admin)):
    return (
        db.query(Rating)
        .filter(Rating.organization_id == admin.organization_id)
        .order_by(Rating.created_at.desc())
        .all()
    )


@router.put("/{rating_id}/mark-reviewed")
def mark_reviewed(rating_id: str, db: Session = Depends(get_db), admin: Account = Depends(_only_org_admin)):
    rating = (
        db.query(Rating)
        .filter(Rating.id == rating_id, Rating.organization_id == admin.organization_id)
        .first()
    )
    if not rating:
        raise HTTPException(404, "غير موجود")
    rating.reviewed = True
    db.commit()
    return {"status": "ok"}


@router.get("/stats", response_model=RatingStats)
def rating_stats(db: Session = Depends(get_db), admin: Account = Depends(_only_org_admin)):
    ratings = db.query(Rating).filter(Rating.organization_id == admin.organization_id).all()
    if not ratings:
        return RatingStats(average_score=0.0, total_ratings=0, per_account={})

    per_account_scores = defaultdict(list)
    for r in ratings:
        per_account_scores[str(r.account_id)].append(r.score)

    per_account_avg = {
        acc_id: round(sum(scores) / len(scores), 2) for acc_id, scores in per_account_scores.items()
    }
    overall_avg = round(sum(r.score for r in ratings) / len(ratings), 2)

    return RatingStats(average_score=overall_avg, total_ratings=len(ratings), per_account=per_account_avg)
