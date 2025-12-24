"""Finance calculator handler - Electricity cost calculation."""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.config import Config
from src.database import Database
from src.keyboards.inline import get_back_button
from src.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

router = Router()

# Global state for dependency injection
_config: Config = None
_db: Database = None


class ElectricityStates(StatesGroup):
    """States for electricity calculation flow."""
    waiting_for_kwh = State()


def setup_finance_router(config: Config, db: Database):
    """Setup finance router with dependencies.
    
    Args:
        config: Application configuration.
        db: Database instance.
    """
    global _config, _db
    _config = config
    _db = db


def calculate_electricity_cost(kwh: float, tariff: Config) -> tuple[float, str]:
    """Calculate electricity cost with progressive tariffs.
    
    Almaty, Kazakhstan progressive tariffs:
    - 0-150 kWh: TARIFF_STEP_1 per kWh
    - 150-300 kWh: TARIFF_STEP_2 per kWh
    - 300+ kWh: TARIFF_STEP_3 per kWh
    
    Args:
        kwh: Kilowatt-hours consumed.
        tariff: Tariff configuration.
        
    Returns:
        tuple[float, str]: (total_cost, breakdown_text)
    """
    total_cost = 0.0
    breakdown = []
    
    if kwh <= 0:
        return 0.0, "Invalid consumption amount"
    
    # First tier: 0-150 kWh
    if kwh > 0:
        tier1_kwh = min(kwh, 150)
        tier1_cost = tier1_kwh * tariff.tariff.step_1
        total_cost += tier1_cost
        breakdown.append(
            f"0\\-150 kWh: {tier1_kwh:.2f} kWh × {tariff.tariff.step_1:.2f} = "
            f"{tier1_cost:.2f} {escape_markdown(tariff.tariff.currency)}"
        )
    
    # Second tier: 150-300 kWh
    if kwh > 150:
        tier2_kwh = min(kwh - 150, 150)
        tier2_cost = tier2_kwh * tariff.tariff.step_2
        total_cost += tier2_cost
        breakdown.append(
            f"150\\-300 kWh: {tier2_kwh:.2f} kWh × {tariff.tariff.step_2:.2f} = "
            f"{tier2_cost:.2f} {escape_markdown(tariff.tariff.currency)}"
        )
    
    # Third tier: 300+ kWh
    if kwh > 300:
        tier3_kwh = kwh - 300
        tier3_cost = tier3_kwh * tariff.tariff.step_3
        total_cost += tier3_cost
        breakdown.append(
            f"300\\+ kWh: {tier3_kwh:.2f} kWh × {tariff.tariff.step_3:.2f} = "
            f"{tier3_cost:.2f} {escape_markdown(tariff.tariff.currency)}"
        )
    
    breakdown_text = "\n".join(breakdown)
    
    return total_cost, breakdown_text


@router.callback_query(F.data == "menu:finance")
async def callback_finance_menu(callback: CallbackQuery, state: FSMContext):
    """Handle finance menu callback.
    
    Args:
        callback: Callback query.
        state: FSM context.
    """
    await _db.log_command(callback.from_user.id, callback.from_user.username, "finance:menu")
    
    await callback.message.edit_text(
        "⚡ *Electricity Cost Calculator*\n\n"
        "*Almaty, Kazakhstan Progressive Tariffs:*\n"
        f"• 0\\-150 kWh: {_config.tariff.step_1:.2f} {escape_markdown(_config.tariff.currency)}/kWh\n"
        f"• 150\\-300 kWh: {_config.tariff.step_2:.2f} {escape_markdown(_config.tariff.currency)}/kWh\n"
        f"• 300\\+ kWh: {_config.tariff.step_3:.2f} {escape_markdown(_config.tariff.currency)}/kWh\n\n"
        "Please enter the electricity consumption in kWh:",
        reply_markup=get_back_button("menu:main"),
        parse_mode="MarkdownV2"
    )
    
    # Set state to wait for input
    await state.set_state(ElectricityStates.waiting_for_kwh)
    await callback.answer()


@router.message(ElectricityStates.waiting_for_kwh)
async def process_kwh_input(message: Message, state: FSMContext):
    """Process kWh input for electricity cost calculation.
    
    Args:
        message: Telegram message.
        state: FSM context.
    """
    try:
        # Parse kWh value
        kwh = float(message.text.replace(',', '.'))
        
        if kwh <= 0:
            await message.answer(
                "⚠️ Please enter a positive number\\.",
                parse_mode="MarkdownV2"
            )
            return
        
        # Calculate cost
        total_cost, breakdown = calculate_electricity_cost(kwh, _config)
        
        # Average cost per kWh
        avg_cost = total_cost / kwh if kwh > 0 else 0
        
        result_text = (
            f"⚡ *Electricity Cost Calculation*\n\n"
            f"*Consumption:* {kwh:.2f} kWh\n\n"
            f"*Breakdown:*\n"
            f"{breakdown}\n\n"
            f"*Total Cost:* {total_cost:.2f} {escape_markdown(_config.tariff.currency)}\n"
            f"*Average Rate:* {avg_cost:.2f} {escape_markdown(_config.tariff.currency)}/kWh\n\n"
            f"_Calculate another amount by entering kWh value\\._"
        )
        
        await message.answer(
            result_text,
            reply_markup=get_back_button("menu:main"),
            parse_mode="MarkdownV2"
        )
        
        # Log command
        await _db.log_command(message.from_user.id, message.from_user.username, f"finance:calculate:{kwh}")
        
    except ValueError:
        await message.answer(
            "⚠️ Invalid input\\. Please enter a numeric value for kWh\\.",
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to calculate electricity cost: {e}")
        await message.answer(
            "❌ *Error*\n\n"
            f"Failed to calculate cost: {escape_markdown(str(e))}",
            parse_mode="MarkdownV2"
        )
        await state.clear()
