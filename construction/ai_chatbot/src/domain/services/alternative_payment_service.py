"""
Alternative Payment Service for Payment Intelligence Domain

Domain service responsible for managing alternative payment options,
payment plans, and flexible payment arrangements for overdue invoices.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from enum import Enum
from abc import ABC, abstractmethod

from ..entities.overdue_invoice import OverdueInvoice, AlternativePaymentOption
from ..aggregates.payment_campaign import PaymentCampaign
from ..value_objects.payment_value_objects import Money, PaymentStatus


class PaymentPlanType(Enum):
    """Types of payment plans available"""
    INSTALLMENT_PLAN = "installment_plan"
    DEFERRED_PAYMENT = "deferred_payment"
    SETTLEMENT_DISCOUNT = "settlement_discount"
    PARTIAL_PAYMENT_ARRANGEMENT = "partial_payment_arrangement"
    HARDSHIP_PLAN = "hardship_plan"
    SEASONAL_PAYMENT_PLAN = "seasonal_payment_plan"


class PaymentMethodType(Enum):
    """Alternative payment methods"""
    ACH_DEBIT = "ach_debit"
    CREDIT_CARD = "credit_card"
    WIRE_TRANSFER = "wire_transfer"
    CHECK_BY_PHONE = "check_by_phone"
    ONLINE_PAYMENT_PORTAL = "online_payment_portal"
    CRYPTOCURRENCY = "cryptocurrency"
    MOBILE_PAYMENT = "mobile_payment"


class DiscountType(Enum):
    """Types of discounts available"""
    EARLY_PAYMENT_DISCOUNT = "early_payment_discount"
    SETTLEMENT_DISCOUNT = "settlement_discount"
    HARDSHIP_DISCOUNT = "hardship_discount"
    PROMPT_PAYMENT_DISCOUNT = "prompt_payment_discount"
    BULK_PAYMENT_DISCOUNT = "bulk_payment_discount"


class IPaymentProcessorService(ABC):
    """Interface for payment processor integration"""
    
    @abstractmethod
    def setup_recurring_payment(self, payment_plan: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    def validate_payment_method(self, payment_method: PaymentMethodType, details: Dict) -> bool:
        pass
    
    @abstractmethod
    def calculate_processing_fees(self, amount: Money, method: PaymentMethodType) -> Money:
        pass


class ICreditPolicyService(ABC):
    """Interface for credit policy integration"""
    
    @abstractmethod
    def get_customer_credit_limits(self, customer_id: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def approve_payment_plan(self, customer_id: str, plan_details: Dict) -> bool:
        pass
    
    @abstractmethod
    def get_discount_authorization_limits(self, user_id: str) -> Dict[str, Decimal]:
        pass


class AlternativePaymentService:
    """
    Domain service for managing alternative payment options and arrangements.
    
    Handles complex business logic around payment plans, discounts,
    and alternative payment methods to improve collection success rates.
    """
    
    def __init__(
        self,
        payment_processor: IPaymentProcessorService,
        credit_policy: ICreditPolicyService
    ):
        self._payment_processor = payment_processor
        self._credit_policy = credit_policy
        
        # Business configuration
        self._max_installments = 12
        self._min_installment_amount = Money(100.0, "USD")
        self._max_settlement_discount = Decimal("0.15")  # 15%
        self._early_payment_discount = Decimal("0.02")   # 2%
        self._hardship_discount_limit = Decimal("0.25")  # 25%
        self._payment_plan_setup_fee = Money(25.0, "USD")
    
    def generate_payment_options(
        self,
        invoice: OverdueInvoice,
        customer_profile: Dict[str, Any]
    ) -> List[AlternativePaymentOption]:
        """Generate available payment options for an overdue invoice"""
        options = []
        
        # Get customer credit information
        credit_info = self._credit_policy.get_customer_credit_limits(invoice.customer_id)
        
        # Generate installment plan options
        installment_options = self._generate_installment_plans(invoice, customer_profile, credit_info)
        options.extend(installment_options)
        
        # Generate settlement discount options
        settlement_options = self._generate_settlement_discounts(invoice, customer_profile)
        options.extend(settlement_options)
        
        # Generate early payment incentives
        early_payment_options = self._generate_early_payment_incentives(invoice, customer_profile)
        options.extend(early_payment_options)
        
        # Generate alternative payment methods
        payment_method_options = self._generate_payment_method_alternatives(invoice, customer_profile)
        options.extend(payment_method_options)
        
        # Generate hardship options if applicable
        if self._qualifies_for_hardship_assistance(invoice, customer_profile):
            hardship_options = self._generate_hardship_options(invoice, customer_profile)
            options.extend(hardship_options)
        
        # Sort options by effectiveness score
        options.sort(key=lambda opt: self._calculate_option_effectiveness(opt, customer_profile), reverse=True)
        
        return options[:10]  # Return top 10 options
    
    def create_payment_plan(
        self,
        invoice: OverdueInvoice,
        plan_type: PaymentPlanType,
        plan_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a formal payment plan for an invoice"""
        
        # Validate plan details
        validation_result = self._validate_payment_plan(invoice, plan_type, plan_details)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": validation_result["error"],
                "plan_id": None
            }
        
        # Get credit approval if required
        if plan_details.get("requires_approval", False):
            approved = self._credit_policy.approve_payment_plan(
                invoice.customer_id,
                plan_details
            )
            if not approved:
                return {
                    "success": False,
                    "error": "Payment plan not approved by credit policy",
                    "plan_id": None
                }
        
        # Create payment plan
        plan_id = self._generate_plan_id()
        
        payment_schedule = self._create_payment_schedule(
            invoice.current_balance,
            plan_type,
            plan_details
        )
        
        # Setup recurring payments if requested
        recurring_payment_id = None
        if plan_details.get("setup_autopay", False):
            recurring_payment_id = self._payment_processor.setup_recurring_payment({
                "plan_id": plan_id,
                "customer_id": invoice.customer_id,
                "schedule": payment_schedule,
                "payment_method": plan_details.get("payment_method")
            })
        
        # Calculate total plan cost including fees
        total_cost = self._calculate_total_plan_cost(invoice.current_balance, plan_details)
        
        return {
            "success": True,
            "plan_id": plan_id,
            "plan_type": plan_type.value,
            "payment_schedule": payment_schedule,
            "total_cost": total_cost,
            "monthly_payment": payment_schedule[0]["amount"] if payment_schedule else None,
            "setup_fee": plan_details.get("setup_fee", Money(0, "USD")),
            "interest_rate": plan_details.get("interest_rate", 0.0),
            "recurring_payment_id": recurring_payment_id,
            "created_at": datetime.utcnow(),
            "terms_accepted": False
        }
    
    def calculate_settlement_offer(
        self,
        invoice: OverdueInvoice,
        customer_profile: Dict[str, Any],
        target_collection_rate: float = 0.85
    ) -> Dict[str, Any]:
        """Calculate optimal settlement offer"""
        
        original_amount = invoice.current_balance.amount
        
        # Base settlement calculation
        days_overdue = invoice.days_overdue
        risk_factor = customer_profile.get("risk_score", 0.5)
        
        # Calculate discount based on various factors
        time_discount = min(days_overdue * 0.002, 0.10)  # Up to 10% for time
        risk_discount = risk_factor * 0.05  # Up to 5% for risk
        base_discount = 0.05  # 5% base settlement discount
        
        total_discount = min(
            time_discount + risk_discount + base_discount,
            self._max_settlement_discount
        )
        
        settlement_amount = original_amount * (1 - total_discount)
        savings = original_amount - settlement_amount
        
        # Calculate payment terms
        payment_deadline = datetime.utcnow() + timedelta(days=14)  # 14 days to accept
        
        return {
            "original_amount": Money(original_amount, invoice.current_balance.currency),
            "settlement_amount": Money(settlement_amount, invoice.current_balance.currency),
            "discount_amount": Money(savings, invoice.current_balance.currency),
            "discount_percentage": total_discount * 100,
            "payment_deadline": payment_deadline,
            "terms": {
                "payment_required_by": payment_deadline,
                "payment_methods_accepted": ["wire_transfer", "certified_check", "ach"],
                "offer_expires": payment_deadline,
                "final_offer": total_discount >= 0.10
            },
            "collection_probability_improvement": self._estimate_settlement_success_rate(
                total_discount, customer_profile
            )
        }
    
    def evaluate_payment_method_suitability(
        self,
        customer_profile: Dict[str, Any],
        payment_amount: Money
    ) -> List[Dict[str, Any]]:
        """Evaluate which payment methods are most suitable for a customer"""
        
        payment_methods = []
        
        # Evaluate each payment method type
        for method_type in PaymentMethodType:
            suitability = self._calculate_method_suitability(
                method_type,
                customer_profile,
                payment_amount
            )
            
            if suitability["score"] > 0.3:  # Only include viable options
                processing_fee = self._payment_processor.calculate_processing_fees(
                    payment_amount,
                    method_type
                )
                
                payment_methods.append({
                    "method_type": method_type.value,
                    "suitability_score": suitability["score"],
                    "advantages": suitability["advantages"],
                    "considerations": suitability["considerations"],
                    "processing_fee": processing_fee,
                    "total_cost": Money(
                        payment_amount.amount + processing_fee.amount,
                        payment_amount.currency
                    ),
                    "setup_time": suitability["setup_time"],
                    "customer_experience_rating": suitability["experience_rating"]
                })
        
        # Sort by suitability score
        payment_methods.sort(key=lambda m: m["suitability_score"], reverse=True)
        
        return payment_methods
    
    def recommend_optimal_payment_strategy(
        self,
        invoice: OverdueInvoice,
        customer_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recommend the optimal payment strategy for maximum collection success"""
        
        # Generate all available options
        payment_options = self.generate_payment_options(invoice, customer_profile)
        
        # Calculate collection probability for each option
        option_analysis = []
        for option in payment_options:
            success_probability = self._estimate_option_success_rate(option, customer_profile)
            expected_collection = option.total_amount.amount * success_probability
            
            option_analysis.append({
                "option": option,
                "success_probability": success_probability,
                "expected_collection": expected_collection,
                "time_to_collection": self._estimate_collection_time(option),
                "customer_satisfaction_impact": self._estimate_satisfaction_impact(option, customer_profile)
            })
        
        # Find optimal strategy
        optimal_option = max(option_analysis, key=lambda o: o["expected_collection"])
        
        # Generate strategy recommendation
        strategy = {
            "recommended_option": optimal_option["option"],
            "expected_collection_amount": Money(optimal_option["expected_collection"], invoice.current_balance.currency),
            "success_probability": optimal_option["success_probability"],
            "estimated_collection_time_days": optimal_option["time_to_collection"],
            "customer_satisfaction_impact": optimal_option["customer_satisfaction_impact"],
            "alternative_options": [o["option"] for o in option_analysis[1:4]],  # Top 3 alternatives
            "strategy_reasoning": self._generate_strategy_reasoning(optimal_option, customer_profile),
            "implementation_steps": self._generate_implementation_steps(optimal_option["option"]),
            "success_metrics": {
                "target_collection_rate": optimal_option["success_probability"],
                "target_collection_amount": optimal_option["expected_collection"],
                "target_days_to_collection": optimal_option["time_to_collection"]
            }
        }
        
        return strategy
    
    # Private helper methods
    
    def _generate_installment_plans(
        self,
        invoice: OverdueInvoice,
        customer_profile: Dict[str, Any],
        credit_info: Dict[str, Any]
    ) -> List[AlternativePaymentOption]:
        """Generate installment plan options"""
        options = []
        
        total_amount = invoice.current_balance.amount
        
        # Generate different installment options
        for months in [3, 6, 9, 12]:
            if months > self._max_installments:
                continue
            
            monthly_payment = total_amount / months
            
            if monthly_payment < self._min_installment_amount.amount:
                continue
            
            # Calculate interest if applicable
            interest_rate = self._calculate_installment_interest_rate(months, customer_profile)
            total_with_interest = total_amount * (1 + interest_rate)
            monthly_with_interest = total_with_interest / months
            
            setup_fee = self._payment_plan_setup_fee if months > 6 else Money(0, "USD")
            
            option = AlternativePaymentOption(
                option_id=f"installment_{months}m",
                option_type="installment_plan",
                description=f"{months}-month installment plan",
                payment_amount=Money(monthly_with_interest, invoice.current_balance.currency),
                total_amount=Money(total_with_interest + setup_fee.amount, invoice.current_balance.currency),
                due_date=datetime.utcnow() + timedelta(days=30),
                terms={
                    "installments": months,
                    "monthly_payment": monthly_with_interest,
                    "interest_rate": interest_rate,
                    "setup_fee": setup_fee.amount,
                    "auto_pay_discount": 0.01 if months >= 6 else 0
                },
                approval_required=months > 6 or total_amount > 5000
            )
            
            options.append(option)
        
        return options
    
    def _generate_settlement_discounts(
        self,
        invoice: OverdueInvoice,
        customer_profile: Dict[str, Any]
    ) -> List[AlternativePaymentOption]:
        """Generate settlement discount options"""
        options = []
        
        # Different discount levels based on payment timing
        discount_scenarios = [
            (7, 0.05),   # 5% discount for 7-day payment
            (14, 0.08),  # 8% discount for 14-day payment
            (30, 0.12),  # 12% discount for 30-day payment
        ]
        
        for days, discount_rate in discount_scenarios:
            if discount_rate > self._max_settlement_discount:
                continue
            
            discounted_amount = invoice.current_balance.amount * (1 - discount_rate)
            savings = invoice.current_balance.amount - discounted_amount
            
            option = AlternativePaymentOption(
                option_id=f"settlement_{days}d_{int(discount_rate*100)}pct",
                option_type="settlement_discount",
                description=f"{int(discount_rate*100)}% settlement discount for {days}-day payment",
                payment_amount=Money(discounted_amount, invoice.current_balance.currency),
                total_amount=Money(discounted_amount, invoice.current_balance.currency),
                due_date=datetime.utcnow() + timedelta(days=days),
                terms={
                    "discount_rate": discount_rate,
                    "savings_amount": savings,
                    "payment_deadline": datetime.utcnow() + timedelta(days=days),
                    "payment_methods": ["wire_transfer", "ach", "certified_check"]
                },
                approval_required=discount_rate > 0.10
            )
            
            options.append(option)
        
        return options
    
    def _generate_early_payment_incentives(
        self,
        invoice: OverdueInvoice,
        customer_profile: Dict[str, Any]
    ) -> List[AlternativePaymentOption]:
        """Generate early payment incentive options"""
        options = []
        
        # Early payment discount for immediate payment
        discount_amount = invoice.current_balance.amount * self._early_payment_discount
        discounted_total = invoice.current_balance.amount - discount_amount
        
        option = AlternativePaymentOption(
            option_id="early_payment_discount",
            option_type="early_payment_incentive",
            description=f"Pay within 3 days and save {self._early_payment_discount*100}%",
            payment_amount=Money(discounted_total, invoice.current_balance.currency),
            total_amount=Money(discounted_total, invoice.current_balance.currency),
            due_date=datetime.utcnow() + timedelta(days=3),
            terms={
                "discount_rate": self._early_payment_discount,
                "savings_amount": discount_amount,
                "payment_deadline": datetime.utcnow() + timedelta(days=3),
                "automatic_processing": True
            },
            approval_required=False
        )
        
        options.append(option)
        
        return options
    
    def _generate_payment_method_alternatives(
        self,
        invoice: OverdueInvoice,
        customer_profile: Dict[str, Any]
    ) -> List[AlternativePaymentOption]:
        """Generate alternative payment method options"""
        options = []
        
        # Online payment portal with convenience
        if customer_profile.get("prefers_online_payments", False):
            option = AlternativePaymentOption(
                option_id="online_payment_portal",
                option_type="payment_method_alternative",
                description="Pay online with credit card or bank transfer",
                payment_amount=invoice.current_balance,
                total_amount=invoice.current_balance,
                due_date=datetime.utcnow() + timedelta(days=7),
                terms={
                    "payment_methods": ["credit_card", "ach", "bank_transfer"],
                    "instant_confirmation": True,
                    "convenience_fee": 2.95  # Fixed convenience fee
                },
                approval_required=False
            )
            options.append(option)
        
        return options
    
    def _qualifies_for_hardship_assistance(
        self,
        invoice: OverdueInvoice,
        customer_profile: Dict[str, Any]
    ) -> bool:
        """Check if customer qualifies for hardship assistance"""
        hardship_indicators = [
            customer_profile.get("financial_hardship_declared", False),
            customer_profile.get("payment_history_decline", False),
            customer_profile.get("recent_business_closure", False),
            customer_profile.get("natural_disaster_impact", False)
        ]
        
        return any(hardship_indicators)
    
    def _generate_hardship_options(
        self,
        invoice: OverdueInvoice,
        customer_profile: Dict[str, Any]
    ) -> List[AlternativePaymentOption]:
        """Generate hardship assistance options"""
        options = []
        
        # Extended payment plan with reduced amount
        hardship_discount = min(
            customer_profile.get("hardship_severity", 0.1),
            self._hardship_discount_limit
        )
        
        reduced_amount = invoice.current_balance.amount * (1 - hardship_discount)
        
        option = AlternativePaymentOption(
            option_id="hardship_assistance",
            option_type="hardship_plan",
            description=f"Hardship assistance with {int(hardship_discount*100)}% reduction",
            payment_amount=Money(reduced_amount / 6, invoice.current_balance.currency),  # 6-month plan
            total_amount=Money(reduced_amount, invoice.current_balance.currency),
            due_date=datetime.utcnow() + timedelta(days=30),
            terms={
                "hardship_discount": hardship_discount,
                "payment_plan_months": 6,
                "no_interest": True,
                "documentation_required": True,
                "review_period": 6  # months
            },
            approval_required=True
        )
        
        options.append(option)
        
        return options
    
    def _calculate_option_effectiveness(
        self,
        option: AlternativePaymentOption,
        customer_profile: Dict[str, Any]
    ) -> float:
        """Calculate effectiveness score for a payment option"""
        base_score = 0.5
        
        # Adjust based on customer preferences
        if option.option_type == "installment_plan" and customer_profile.get("prefers_payment_plans", False):
            base_score += 0.3
        
        if option.option_type == "settlement_discount" and customer_profile.get("responds_to_discounts", False):
            base_score += 0.2
        
        # Adjust based on payment amount
        affordability_ratio = option.payment_amount.amount / customer_profile.get("monthly_payment_capacity", 1000)
        if affordability_ratio <= 0.5:
            base_score += 0.2
        elif affordability_ratio > 1.0:
            base_score -= 0.3
        
        return min(max(base_score, 0.0), 1.0)
    
    def _validate_payment_plan(
        self,
        invoice: OverdueInvoice,
        plan_type: PaymentPlanType,
        plan_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate payment plan details"""
        
        # Basic validation
        if plan_details.get("installments", 0) > self._max_installments:
            return {
                "valid": False,
                "error": f"Maximum {self._max_installments} installments allowed"
            }
        
        monthly_payment = plan_details.get("monthly_payment", 0)
        if monthly_payment < self._min_installment_amount.amount:
            return {
                "valid": False,
                "error": f"Minimum monthly payment of {self._min_installment_amount.amount} required"
            }
        
        return {"valid": True, "error": None}
    
    def _generate_plan_id(self) -> str:
        """Generate unique payment plan ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"PP{timestamp}"
    
    def _create_payment_schedule(
        self,
        total_amount: Money,
        plan_type: PaymentPlanType,
        plan_details: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create payment schedule for a plan"""
        schedule = []
        
        installments = plan_details.get("installments", 3)
        monthly_payment = total_amount.amount / installments
        
        for month in range(installments):
            due_date = datetime.utcnow() + timedelta(days=30 * (month + 1))
            
            schedule.append({
                "installment_number": month + 1,
                "amount": Money(monthly_payment, total_amount.currency),
                "due_date": due_date,
                "status": "pending"
            })
        
        return schedule
    
    def _calculate_total_plan_cost(
        self,
        original_amount: Money,
        plan_details: Dict[str, Any]
    ) -> Money:
        """Calculate total cost of payment plan including fees and interest"""
        base_amount = original_amount.amount
        
        # Add interest
        interest_rate = plan_details.get("interest_rate", 0.0)
        interest_amount = base_amount * interest_rate
        
        # Add setup fee
        setup_fee = plan_details.get("setup_fee", Money(0, original_amount.currency)).amount
        
        total_cost = base_amount + interest_amount + setup_fee
        
        return Money(total_cost, original_amount.currency)
    
    def _calculate_installment_interest_rate(
        self,
        months: int,
        customer_profile: Dict[str, Any]
    ) -> float:
        """Calculate interest rate for installment plan"""
        base_rate = 0.02  # 2% base rate
        
        # Adjust based on term length
        term_adjustment = (months - 3) * 0.005  # 0.5% per month over 3
        
        # Adjust based on customer risk
        risk_adjustment = customer_profile.get("risk_score", 0.5) * 0.03
        
        return base_rate + term_adjustment + risk_adjustment
    
    def _calculate_method_suitability(
        self,
        method_type: PaymentMethodType,
        customer_profile: Dict[str, Any],
        payment_amount: Money
    ) -> Dict[str, Any]:
        """Calculate suitability score for a payment method"""
        
        base_score = 0.5
        advantages = []
        considerations = []
        
        if method_type == PaymentMethodType.CREDIT_CARD:
            advantages = ["Instant processing", "Customer convenience", "Rewards points"]
            considerations = ["Processing fees", "Credit limit requirements"]
            base_score += 0.2 if payment_amount.amount < 5000 else -0.1
            
        elif method_type == PaymentMethodType.ACH_DEBIT:
            advantages = ["Low processing fees", "Reliable collection", "Recurring capability"]
            considerations = ["Bank account required", "Processing delay"]
            base_score += 0.3
            
        elif method_type == PaymentMethodType.WIRE_TRANSFER:
            advantages = ["Immediate settlement", "High security", "Large amount capability"]
            considerations = ["Higher fees", "Bank visit required"]
            base_score += 0.2 if payment_amount.amount > 10000 else -0.2
        
        # Adjust based on customer preferences
        preferred_methods = customer_profile.get("preferred_payment_methods", [])
        if method_type.value in preferred_methods:
            base_score += 0.2
        
        return {
            "score": min(max(base_score, 0.0), 1.0),
            "advantages": advantages,
            "considerations": considerations,
            "setup_time": self._get_method_setup_time(method_type),
            "experience_rating": self._get_method_experience_rating(method_type)
        }
    
    def _get_method_setup_time(self, method_type: PaymentMethodType) -> str:
        """Get typical setup time for payment method"""
        setup_times = {
            PaymentMethodType.CREDIT_CARD: "Immediate",
            PaymentMethodType.ACH_DEBIT: "1-2 business days",
            PaymentMethodType.WIRE_TRANSFER: "Same day",
            PaymentMethodType.ONLINE_PAYMENT_PORTAL: "Immediate",
            PaymentMethodType.CHECK_BY_PHONE: "Same day",
            PaymentMethodType.MOBILE_PAYMENT: "Immediate"
        }
        return setup_times.get(method_type, "1-3 business days")
    
    def _get_method_experience_rating(self, method_type: PaymentMethodType) -> float:
        """Get customer experience rating for payment method"""
        ratings = {
            PaymentMethodType.CREDIT_CARD: 4.5,
            PaymentMethodType.ACH_DEBIT: 4.0,
            PaymentMethodType.ONLINE_PAYMENT_PORTAL: 4.7,
            PaymentMethodType.MOBILE_PAYMENT: 4.6,
            PaymentMethodType.WIRE_TRANSFER: 3.5,
            PaymentMethodType.CHECK_BY_PHONE: 3.8
        }
        return ratings.get(method_type, 3.5)
    
    def _estimate_settlement_success_rate(
        self,
        discount_rate: float,
        customer_profile: Dict[str, Any]
    ) -> float:
        """Estimate success rate for settlement offer"""
        base_rate = 0.6  # 60% base success rate
        
        # Higher discount = higher success rate
        discount_bonus = discount_rate * 2  # 2x discount rate as bonus
        
        # Customer responsiveness factor
        responsiveness = customer_profile.get("payment_responsiveness", 0.5)
        
        # Financial capability factor
        financial_capability = customer_profile.get("financial_capability", 0.5)
        
        success_rate = base_rate + discount_bonus + (responsiveness * 0.2) + (financial_capability * 0.1)
        
        return min(max(success_rate, 0.1), 0.95)
    
    def _estimate_option_success_rate(
        self,
        option: AlternativePaymentOption,
        customer_profile: Dict[str, Any]
    ) -> float:
        """Estimate success rate for a payment option"""
        base_rates = {
            "installment_plan": 0.75,
            "settlement_discount": 0.65,
            "early_payment_incentive": 0.80,
            "hardship_plan": 0.70,
            "payment_method_alternative": 0.60
        }
        
        base_rate = base_rates.get(option.option_type, 0.50)
        
        # Adjust based on customer profile
        payment_history = customer_profile.get("payment_history_score", 0.5)
        adjustment = (payment_history - 0.5) * 0.2
        
        return min(max(base_rate + adjustment, 0.1), 0.95)
    
    def _estimate_collection_time(self, option: AlternativePaymentOption) -> int:
        """Estimate days to collection for an option"""
        collection_times = {
            "early_payment_incentive": 3,
            "settlement_discount": 14,
            "payment_method_alternative": 7,
            "installment_plan": 90,  # Average of plan duration
            "hardship_plan": 180
        }
        
        return collection_times.get(option.option_type, 30)
    
    def _estimate_satisfaction_impact(
        self,
        option: AlternativePaymentOption,
        customer_profile: Dict[str, Any]
    ) -> str:
        """Estimate customer satisfaction impact"""
        
        if option.option_type in ["hardship_plan", "installment_plan"]:
            return "Positive - shows flexibility and understanding"
        elif option.option_type == "settlement_discount":
            return "Neutral to Positive - provides financial relief"
        elif option.option_type == "early_payment_incentive":
            return "Positive - rewards prompt payment"
        else:
            return "Neutral - provides payment convenience"
    
    def _generate_strategy_reasoning(
        self,
        optimal_option: Dict[str, Any],
        customer_profile: Dict[str, Any]
    ) -> str:
        """Generate reasoning for strategy recommendation"""
        
        option = optimal_option["option"]
        success_prob = optimal_option["success_probability"]
        
        reasoning = f"Recommended {option.option_type} based on {success_prob:.1%} success probability. "
        
        if option.option_type == "installment_plan":
            reasoning += "Customer profile indicates preference for manageable monthly payments. "
        elif option.option_type == "settlement_discount":
            reasoning += "Customer shows high responsiveness to financial incentives. "
        
        reasoning += f"Expected collection of {optimal_option['expected_collection']:.2f} "
        reasoning += f"within {optimal_option['time_to_collection']} days."
        
        return reasoning
    
    def _generate_implementation_steps(self, option: AlternativePaymentOption) -> List[str]:
        """Generate implementation steps for a payment option"""
        
        steps = [
            f"1. Send {option.option_type} offer to customer",
            "2. Provide clear payment instructions and deadlines",
            "3. Set up payment tracking and reminders"
        ]
        
        if option.approval_required:
            steps.insert(1, "1.5. Obtain required approvals")
        
        if option.option_type == "installment_plan":
            steps.append("4. Set up recurring payment processing")
            steps.append("5. Monitor payment schedule compliance")
        
        elif option.option_type == "settlement_discount":
            steps.append("4. Confirm payment receipt within deadline")
            steps.append("5. Process account closure upon payment")
        
        return steps