import json
from datetime import datetime
from sqlalchemy.orm import Session
from models.token_usage import TokenUsage
from config.database import SessionLocal


class TokenUsageService:
    """Service để log token usage từ API calls"""
    
    @staticmethod
    async def log_token_usage(
        session_id: int = None,
        usage_type: str = "llm_api",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        db: Session = None
    ):
        """
        Log token usage vào database
        
        Args:
            session_id: ID của assistant session (optional)
            usage_type: Loại usage (default: "llm_api")
            prompt_tokens: Số tokens của input
            completion_tokens: Số tokens của output
            total_tokens: Tổng tokens
            db: Database session (optional, sẽ create mới nếu không có)
        
        Returns:
            TokenUsage instance hoặc None nếu không tạo được
        """
        try:
            # Nếu không có session_id, chỉ log console
            if session_id is None:
                print(f"⚠️  [Token Usage] No session_id provided, skipping DB logging")
                print(f"   Type: {usage_type} | Tokens: {total_tokens} ({prompt_tokens}→{completion_tokens})")
                return None
            
            # Create session nếu không có
            if db is None:
                db = SessionLocal()
                should_close = True
            else:
                should_close = False
            
            try:
                # Metadata chứa chi tiết
                metadata = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Tạo record
                token_usage = TokenUsage(
                    session_id=session_id,
                    usage_type=usage_type,
                    amount=total_tokens,
                    metadata=json.dumps(metadata)
                )
                
                db.add(token_usage)
                db.commit()
                db.refresh(token_usage)
                
                print(f"✓ [Token Usage] Logged: {total_tokens} tokens | Session: {session_id}")
                return token_usage
                
            finally:
                if should_close:
                    db.close()
        
        except Exception as e:
            print(f"✗ [Token Usage] Error logging usage: {str(e)}")
            return None
    
    @staticmethod
    async def get_session_usage(session_id: int, db: Session = None) -> dict:
        """
        Lấy tổng token usage của một session
        
        Returns:
            Dict chứa total_tokens, total_cost, usage_details
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
                
                total_tokens = sum(u.amount for u in usages)
                total_cost = 0
                
                for usage in usages:
                    try:
                        metadata = json.loads(usage.metadata) if usage.metadata else {}
                        if "cost" in metadata:
                            total_cost += metadata["cost"]
                    except:
                        pass
                
                return {
                    "session_id": session_id,
                    "total_tokens": total_tokens,
                    "total_cost": total_cost,
                    "usage_count": len(usages),
                    "usages": [
                        {
                            "usage_id": u.usage_id,
                            "type": u.usage_type,
                            "tokens": u.amount,
                            "metadata": json.loads(u.metadata) if u.metadata else {},
                            "created_at": u.created_at.isoformat()
                        }
                        for u in usages
                    ]
                }
            finally:
                if should_close:
                    db.close()
        
        except Exception as e:
            print(f"✗ [Token Usage] Error getting usage: {str(e)}")
            return None


# Global instance để sử dụng dễ
token_usage_service = TokenUsageService()
