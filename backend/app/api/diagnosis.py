from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.core.database import get_db
from app.models.schemas import DiagnosisMetrics, DiagnosisAnalysis
from app.models.db_models import Order, User, Product
from app.services.diagnosis_service import diagnosis_service
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])


@router.get("/summary")
async def get_diagnosis_summary(db: Session = Depends(get_db)):
    """获取诊断总结 - 基于真实数据库数据"""
    
    # 计算真实指标
    metrics = await calculate_real_metrics(db)
    analysis = await diagnosis_service.analyze_metrics(metrics)

    return {
        "total_issues": analysis["total_issues"],
        "high_priority": sum(1 for i in analysis["issues"] if i.get("severity") == "high"),
        "medium_priority": sum(1 for i in analysis["issues"] if i.get("severity") == "medium"),
        "low_priority": sum(1 for i in analysis["issues"] if i.get("severity") == "low"),
        "generated_at": datetime.now(),
        "metrics": metrics,  # 同时返回真实指标
    }


@router.get("/metrics", response_model=DiagnosisMetrics)
async def get_diagnosis_metrics(db: Session = Depends(get_db)):
    """获取诊断指标 - 基于真实数据库数据"""
    
    metrics = await calculate_real_metrics(db)
    today = datetime.now().strftime("%Y-%m-%d")
    
    return {
        "order_metrics": {
            "name": "订单总数",
            "value": metrics["order_count"],
            "date": today,
        },
        "gmv_metrics": {
            "name": "GMV",
            "value": metrics["gmv"],
            "date": today,
        },
        "conversion_metrics": {
            "name": "转化率(%)",
            "value": metrics["conversion_rate"],
            "date": today,
        },
        "user_active_metrics": {
            "name": "活跃用户",
            "value": metrics["active_users"],
            "date": today,
        },
    }


@router.get("/analyze/{metric_name}", response_model=DiagnosisAnalysis)
async def analyze_metric(
    metric_name: str,
    db: Session = Depends(get_db),
):
    """深度分析某个指标 - 基于真实数据"""
    
    # 获取真实指标数据
    metrics = await calculate_real_metrics(db)
    
    # 根据指标名称进行特定分析
    if metric_name == "order_count":
        # 分析订单趋势
        trend = await get_order_trend(db)
        issue = "订单量分析" if metrics["order_count"] >= 500 else "订单量偏低"
        root_cause = await analyze_order_issues(db, metrics)
        recommendation = await generate_order_recommendations(db, metrics)
        priority = "medium" if metrics["order_count"] >= 500 else "high"
        
    elif metric_name == "gmv":
        # 分析GMV
        issue = "GMV分析" if metrics["gmv"] >= 100000 else "GMV偏低"
        root_cause = f"当前GMV为 {metrics['gmv']:.2f} 元，需要结合订单量和客单价综合分析"
        recommendation = "建议提升客单价或增加订单量"
        priority = "medium"
        
    elif metric_name == "conversion_rate":
        # 分析转化率
        issue = "转化率分析"
        root_cause = f"当前转化率为 {metrics['conversion_rate']:.2f}%"
        if metrics["conversion_rate"] < 2.0:
            root_cause += "，低于行业平均水平，可能存在用户体验或产品吸引力问题"
            priority = "high"
        else:
            root_cause += "，处于正常水平"
            priority = "low"
        recommendation = "优化产品页面、简化购买流程、提供促销活动"
        
    elif metric_name == "active_users":
        # 分析活跃用户
        issue = "活跃用户分析"
        if metrics["active_users"] < 3000:
            issue = "活跃用户数偏低"
            root_cause = f"当前活跃用户数为 {metrics['active_users']}，低于预期"
            recommendation = "加强用户运营、提升产品粘性、开展拉新活动"
            priority = "high"
        else:
            root_cause = f"当前活跃用户数为 {metrics['active_users']}，表现良好"
            recommendation = "继续保持用户活跃度"
            priority = "low"
    else:
        issue = f"{metric_name} 分析"
        root_cause = "暂无详细数据"
        recommendation = "建议关注该指标变化趋势"
        priority = "medium"

    return {
        "issue": issue,
        "root_cause": root_cause,
        "recommendation": recommendation,
        "priority": priority,
        "current_value": metrics.get(metric_name.replace("_metrics", ""), 0),
    }


async def calculate_real_metrics(db: Session) -> dict:
    """计算真实业务指标"""
    
    # 1. 订单总数
    order_count = db.query(func.count(Order.id)).scalar() or 0
    
    # 2. GMV (总交易额)
    gmv = db.query(func.sum(Order.amount)).scalar() or 0.0
    
    # 3. 用户总数
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # 4. 活跃用户（有订单的用户）
    active_users = db.query(func.count(func.distinct(Order.user_id))).scalar() or 0
    
    # 5. 转化率 = 下单用户数 / 总用户数 * 100
    conversion_rate = (active_users / total_users * 100) if total_users > 0 else 0
    
    # 6. 客单价
    avg_order_value = (gmv / order_count) if order_count > 0 else 0
    
    # 7. 商品总数
    product_count = db.query(func.count(Product.id)).scalar() or 0
    
    # 8. 库存紧张商品数
    low_stock_count = db.query(func.count(Product.id)).filter(Product.stock < 10).scalar() or 0
    
    return {
        "order_count": order_count,
        "gmv": round(gmv, 2),
        "conversion_rate": round(conversion_rate, 2),
        "active_users": active_users,
        "total_users": total_users,
        "avg_order_value": round(avg_order_value, 2),
        "product_count": product_count,
        "low_stock_count": low_stock_count,
    }


async def get_order_trend(db: Session) -> dict:
    """获取订单趋势（最近7天）"""
    today = datetime.now()
    dates = []
    counts = []
    
    for i in range(7):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        # 查询当天的订单数
        count = db.query(func.count(Order.id)).filter(
            func.date(Order.created_at) == date_str
        ).scalar() or 0
        
        dates.insert(0, date_str)
        counts.insert(0, count)
    
    return {
        "dates": dates,
        "counts": counts,
        "trend": "上升" if counts[-1] > counts[0] else "下降" if counts[-1] < counts[0] else "平稳"
    }


async def analyze_order_issues(db: Session, metrics: dict) -> str:
    """分析订单相关问题"""
    issues = []
    
    if metrics["order_count"] < 500:
        issues.append("订单总量偏低")
    
    if metrics["avg_order_value"] < 100:
        issues.append("客单价较低")
    
    # 查询待处理订单数
    pending_orders = db.query(func.count(Order.id)).filter(Order.status == "pending").scalar() or 0
    if pending_orders > 10:
        issues.append(f"有 {pending_orders} 个待处理订单积压")
    
    if not issues:
        return "订单指标正常"
    
    return "; ".join(issues)


async def generate_order_recommendations(db: Session, metrics: dict) -> str:
    """生成订单相关建议"""
    recommendations = []
    
    if metrics["order_count"] < 500:
        recommendations.append("开展促销活动提升订单量")
        recommendations.append("优化产品推荐算法")
    
    if metrics["avg_order_value"] < 100:
        recommendations.append("推出满减活动提升客单价")
        recommendations.append("优化产品组合销售")
    
    if not recommendations:
        recommendations.append("保持当前运营策略")
        recommendations.append("持续监控订单趋势")
    
    return "; ".join(recommendations)
