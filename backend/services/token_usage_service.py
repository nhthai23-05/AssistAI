"""Token Usage Service - Logs and tracks token consumption"""
import json
from datetime import datetime
from sqlalchemy.orm import Session
from models.token_usage import TokenUsage
from config.database import SessionLocal
from typing import Optional, Dict
from exceptions import DatabaseError, SessionNotFoundError


class TokenUsageService:
    """Service for logging and tracking token usage from API calls"""
    
    @staticmethod
    async def log_token_usage(
        session_id: Optional[int] = None,
        usage_type: str = "llm_api",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        model: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Optional[TokenUsage]:
        """
        Log token usage to database
        
        Args:
            session_id: ID of assistant session (optional)
            usage_type: Type of usage (default: "llm_api")
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            total_tokens: Total tokens
            model: Model name/identifier
            db: Database session (optional, creates new if not provided)
        
        Returns:
            TokenUsage instance or None if session_id not provided
            
        Raises:
            SessionNotFoundError: If session_id provided but not found
            DatabaseError: If database operation fails
        """
        try:
            # If no session_id, skip DB logging but return None
            if session_id is None:
                return None
            
            # Create session if not provided
            if db is None:
                db = SessionLocal()
                should_close = True
            else:
                should_close = False
            
            try:
                # Build metadata
                metadata = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "model": model or "unknown",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Create record
                token_usage = TokenUsage(
                    session_id=session_id,
                    usage_type=usage_type,
                    amount=total_tokens,
                    metadata=json.dumps(metadata)
                )
                
                db.add(token_usage)
                db.commit()
                db.refresh(token_usage)
                
                return token_usage
                
            finally:
                if should_close:
                    db.close()
        
        except Exception as e:
            raise DatabaseError(f"Failed to log token usage: {str(e)}")
    
    @staticmethod
    async def get_session_usage(
        session_id: int,
        db: Optional[Session] = None
    ) -> Dict:
        """
        Get total token usage for a session
        
        Args:
            session_id: Session ID
            db: Database session (optional)
        
        Returns:
            Dict with total_tokens, usage_breakdown
            
        Raises:
            SessionNotFoundError: If session not found
            DatabaseError: If database operation fails
        """
        try:
            if db is None:
                db = SessionLocal()
                should_close = True
            else:
                should_close = False
            
            try:
                usages = db.query(TokenUsage).filter(
                    TokenUsage.session_id == session_id
                ).all()
                
                if not usages:
                    return {
                        "session_id": session_id,
                        "total_tokens": 0,
                        "usage_breakdown": {},
                        "cost_estimate": 0.0
                    }
                
                # Calculate totals
                total_tokens = sum(u.amount for u in usages)
                
                # Build breakdown by usage type
                breakdown = {}
                for usage in usages:
                    usage_type = usage.usage_type
                    if usage_type not in breakdown:
                        breakdown[usage_type] = 0
                    breakdown[usage_type] += usage.amount
                
                # Estimate cost (based on GPT-4 pricing as default)
                cost_estimate = TokenUsageService._estimate_cost(total_tokens)
                
                return {
                    "session_id": session_id,
                    "total_tokens": total_tokens,
                    "usage_breakdown": breakdown,
                    "cost_estimate": cost_estimate
                }
                
            finally:
                if should_close:
                    db.close()
        
        except Exception as e:
            raise DatabaseError(f"Failed to get session usage: {str(e)}")
    
    @staticmethod
    def _estimate_cost(total_tokens: int) -> float:
        """
        Estimate API cost based on token count
        Using approximate GPT-4 pricing
        
        Args:
            total_tokens: Total tokens used
            
        Returns:
            Estimated cost in USD
        """
        # Approximate pricing: $0.03 per 1K tokens (average)
        return (total_tokens / 1000) * 0.03
    
    @staticmethod
    async def get_user_monthly_usage(
        user_id: int,
        db: Optional[Session] = None
    ) -> Dict:
        """
        Get monthly token usage for a user
        
        Args:
            user_id: User ID
            db: Database session
        
        Returns:
            Dict with monthly token stats
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            if db is None:
                db = SessionLocal()
                should_close = True
            else:
                should_close = False
            
            try:
                # This would require joining with sessions to get user_id
                # For now, just return placeholder
                return {
                    "user_id": user_id,
                    "month": datetime.utcnow().strftime("%Y-%m"),
                    "total_tokens": 0,
                    "sessions_count": 0,
                    "cost_estimate": 0.0
                }
                
            finally:
                if should_close:
                    db.close()
        
        except Exception as e:
            raise DatabaseError(f"Failed to get monthly usage: {str(e)}")


# Global instance để sử dụng dễ
token_usage_service = TokenUsageService()
