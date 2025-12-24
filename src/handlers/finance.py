"""Finance handler for electricity cost calculation."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from src.utils.formatters import escape_markdown_v2

router = Router()


@router.message(Command("cost"))
async def calculate_cost(message: Message, config, db) -> None:
    """Calculate electricity cost based on Almaty tariffs."""
    try:
        # Log command
        await db.log_command(
            user_id=message.from_user.id,
            username=message.from_user.username,
            command="cost"
        )
        
        args = message.text.split()[1:]
        if len(args) != 2:
            await message.answer(
                escape_markdown_v2("❌ Использование: /cost <watts> <hours>\n"
                               "Пример: /cost 350 720 (350W за 30 дней)"),
                parse_mode="MarkdownV2"
            )
            return
        
        watts = float(args[0])
        hours = float(args[1])
        
        # Calculate kWh
        kwh = (watts / 1000) * hours
        
        # Progressive tariff calculation (Almaty)
        tariff_1 = config.TARIFF_STEP_1
        tariff_2 = config.TARIFF_STEP_2
        tariff_3 = config.TARIFF_STEP_3
        currency = config.CURRENCY
        
        if kwh <= 150:
            cost = kwh * tariff_1
        elif kwh <= 300:
            cost = 150 * tariff_1 + (kwh - 150) * tariff_2
        else:
            cost = 150 * tariff_1 + 150 * tariff_2 + (kwh - 300) * tariff_3
        
        response = (
            f"💰 *Калькулятор электроэнергии*\n\n"
            f"⚡ Мощность: {watts} Вт\n"
            f"⏱ Время: {hours} ч \\({hours/24:.1f} дней\\)\n"
            f"📊 Потребление: {kwh:.2f} кВт⋅ч\n\n"
            f"💵 *Стоимость:* {cost:.2f} {currency}\n\n"
            f"_Тарифы Алматы \\(2025\\):_\n"
            f"• 0\\-150 кВт⋅ч: {tariff_1} {currency}\n"
            f"• 150\\-300 кВт⋅ч: {tariff_2} {currency}\n"
            f"• 300\\+ кВт⋅ч: {tariff_3} {currency}"
        )
        
        await message.answer(response, parse_mode="MarkdownV2")
        
    except (ValueError, IndexError):
        await message.answer(
            escape_markdown_v2("❌ Ошибка: введите корректные числа"),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        await message.answer(
            escape_markdown_v2(f"❌ Ошибка: {str(e)}"),
            parse_mode="MarkdownV2"
        )
