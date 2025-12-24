"""
Finance handlers for electricity cost calculation.
"""
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.config import config
from src.database.db import Database
from src.keyboards.inline import get_back_keyboard
from src.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

router = Router()

# Global instances (will be set in main.py)
db: Optional[Database] = None


def set_services(database: Database) -> None:
    """Set global service instances."""
    global db
    db = database


class FinanceStates(StatesGroup):
    """States for finance calculator."""
    waiting_for_kwh = State()
    waiting_for_power = State()


@router.callback_query(F.data == "menu_finance")
async def menu_finance(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle finance menu callback.
    
    Args:
        callback: Callback query object
        state: FSM context
    """
    # Clear any existing state
    await state.clear()
    
    text = (
        "💰 *Electricity Cost Calculator*\n\n"
        "*Almaty Tariff \\(Progressive\\):*\n"
        f"• 0\\-150 kWh: {config.TARIFF_STEP_1} {config.CURRENCY}/kWh\n"
        f"• 150\\-300 kWh: {config.TARIFF_STEP_2} {config.CURRENCY}/kWh\n"
        f"• 300\\+ kWh: {config.TARIFF_STEP_3} {config.CURRENCY}/kWh\n\n"
        "Please send the total kWh consumed to calculate the cost\\.\n\n"
        "_Example: 250_"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=get_back_keyboard("main_menu")
    )
    
    # Set state
    await state.set_state(FinanceStates.waiting_for_kwh)
    await callback.answer()


@router.message(FinanceStates.waiting_for_kwh)
async def process_kwh(message: Message, state: FSMContext) -> None:
    """
    Process kWh input and calculate cost.
    
    Args:
        message: Message object
        state: FSM context
    """
    try:
        # Parse kWh
        kwh = float(message.text.strip())
        
        if kwh < 0:
            await message.answer(
                "❌ Please enter a positive number\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        # Calculate cost with progressive tariff
        cost = 0.0
        breakdown = []
        
        if kwh <= 150:
            # All consumption in first tier
            cost = kwh * config.TARIFF_STEP_1
            breakdown.append(f"• {kwh:.2f} kWh × {config.TARIFF_STEP_1} = {cost:.2f} {config.CURRENCY}")
        elif kwh <= 300:
            # First 150 kWh in tier 1, rest in tier 2
            tier1_cost = 150 * config.TARIFF_STEP_1
            tier2_kwh = kwh - 150
            tier2_cost = tier2_kwh * config.TARIFF_STEP_2
            cost = tier1_cost + tier2_cost
            
            breakdown.append(f"• 150 kWh × {config.TARIFF_STEP_1} = {tier1_cost:.2f} {config.CURRENCY}")
            breakdown.append(f"• {tier2_kwh:.2f} kWh × {config.TARIFF_STEP_2} = {tier2_cost:.2f} {config.CURRENCY}")
        else:
            # All three tiers
            tier1_cost = 150 * config.TARIFF_STEP_1
            tier2_cost = 150 * config.TARIFF_STEP_2
            tier3_kwh = kwh - 300
            tier3_cost = tier3_kwh * config.TARIFF_STEP_3
            cost = tier1_cost + tier2_cost + tier3_cost
            
            breakdown.append(f"• 150 kWh × {config.TARIFF_STEP_1} = {tier1_cost:.2f} {config.CURRENCY}")
            breakdown.append(f"• 150 kWh × {config.TARIFF_STEP_2} = {tier2_cost:.2f} {config.CURRENCY}")
            breakdown.append(f"• {tier3_kwh:.2f} kWh × {config.TARIFF_STEP_3} = {tier3_cost:.2f} {config.CURRENCY}")
        
        # Calculate average cost per kWh
        avg_cost = cost / kwh if kwh > 0 else 0
        
        # Format output
        text = "💰 *Electricity Cost Calculation*\n\n"
        text += f"*Total Consumption:* {kwh:.2f} kWh\n\n"
        text += "*Breakdown:*\n"
        
        for line in breakdown:
            text += f"{escape_markdown(line)}\n"
        
        text += f"\n*Total Cost:* {cost:.2f} {config.CURRENCY}\n"
        text += f"*Average Rate:* {avg_cost:.2f} {config.CURRENCY}/kWh\n\n"
        
        # Add monthly estimate if input seems to be daily
        if kwh < 50:
            monthly_kwh = kwh * 30
            monthly_cost = calculate_progressive_cost(monthly_kwh)
            text += f"\n_If this is daily usage:_\n"
            text += f"Monthly: {monthly_kwh:.0f} kWh ≈ {monthly_cost:.2f} {config.CURRENCY}\n"
        
        # Log action
        if db:
            await db.log_command(
                message.from_user.id,
                message.from_user.username,
                f"finance_calc_{kwh}"
            )
        
        await message.answer(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_back_keyboard("main_menu")
        )
        
        # Clear state
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Invalid input\\. Please enter a number\\.\n\n"
            "_Example: 250_",
            parse_mode="MarkdownV2"
        )


def calculate_progressive_cost(kwh: float) -> float:
    """
    Calculate electricity cost with progressive tariff.
    
    Args:
        kwh: Consumption in kWh
        
    Returns:
        Total cost
    """
    cost = 0.0
    
    if kwh <= 150:
        cost = kwh * config.TARIFF_STEP_1
    elif kwh <= 300:
        cost = 150 * config.TARIFF_STEP_1
        cost += (kwh - 150) * config.TARIFF_STEP_2
    else:
        cost = 150 * config.TARIFF_STEP_1
        cost += 150 * config.TARIFF_STEP_2
        cost += (kwh - 300) * config.TARIFF_STEP_3
    
    return cost
