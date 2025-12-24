"""Finance calculator handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from src.keyboards.inline import back_button
from src.utils.formatters import escape_markdown_v2

logger = logging.getLogger(__name__)

router = Router()


class FinanceStates(StatesGroup):
    """States for finance calculator."""
    waiting_for_power = State()


@router.callback_query(F.data == "menu_finance")
async def show_finance_menu(callback: CallbackQuery, config, proxmox, db) -> None:
    """Show finance calculator."""
    try:
        await callback.answer("Calculating...")
        
        # Log command
        await db.log_command(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            command="menu_finance"
        )
        
        # Get all nodes
        nodes = await proxmox.get_nodes()
        
        text = "💰 *Electricity Cost Calculator*\n\n"
        text += f"*Electricity Rate:* {config.ELECTRICITY_RATE} KZT/kWh \\(Almaty\\)\n\n"
        
        if not nodes:
            text += "No nodes found to calculate costs\\."
        else:
            total_power_estimate = 0
            
            for node_info in nodes:
                node = node_info['node']
                
                # Get VMs on node
                vms = await proxmox.get_vms(node)
                running_vms = [vm for vm in vms if vm.get('status') == 'running']
                
                # Estimate power consumption
                # Rough estimate: Base system 50W + 10W per running VM
                node_power = 50 + (len(running_vms) * 10)
                total_power_estimate += node_power
                
                text += f"*Node:* {escape_markdown_v2(node)}\n"
                text += f"  Running VMs: {len(running_vms)}\n"
                text += f"  Estimated Power: ~{node_power}W\n\n"
            
            # Calculate costs
            daily_kwh = (total_power_estimate * 24) / 1000
            daily_cost = daily_kwh * config.ELECTRICITY_RATE
            monthly_cost = daily_cost * 30
            yearly_cost = daily_cost * 365
            
            text += "*Estimated Costs:*\n"
            text += f"Power Consumption: ~{total_power_estimate}W\n"
            text += f"Daily: {daily_kwh:.2f} kWh = {daily_cost:.2f} KZT\n"
            text += f"Monthly: {daily_kwh * 30:.2f} kWh = {monthly_cost:.2f} KZT\n"
            text += f"Yearly: {daily_kwh * 365:.2f} kWh = {yearly_cost:.2f} KZT\n\n"
            text += "_Note: These are rough estimates\\. Actual power consumption may vary\\._"
        
        await callback.message.edit_text(
            text,
            reply_markup=back_button("menu_main"),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing finance calculator: {e}", exc_info=True)
        await callback.answer("Error calculating costs", show_alert=True)
