from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import db  # Ensure this database module is correctly implemented
from pyromod.exceptions import ListenerTimeout
from config import Txt

# Inline button setups for metadata ON and OFF with custom option
ON = [[InlineKeyboardButton('Metadata On ✅', callback_data='metadata_1')],
      [InlineKeyboardButton('Set Custom Metadata', callback_data='custom_metadata')]]
OFF = [[InlineKeyboardButton('Metadata Off ❌', callback_data='metadata_0')],
       [InlineKeyboardButton('Set Custom Metadata', callback_data='custom_metadata')]]


@Client.on_message(filters.private & filters.command('metadata'))
async def handle_metadata(bot: Client, message: Message):
    # Initial response to indicate processing
    ms = await message.reply_text("**Please Wait...**", reply_to_message_id=message.id)
    
    # Retrieve metadata status and current metadata code
    bool_metadata = await db.get_metadata(message.from_user.id)
    user_metadata = await db.get_metadata_code(message.from_user.id)
    
    await ms.delete()  # Delete the processing message
    
    # Show the current metadata status and buttons for user interaction
    if bool_metadata:
        await message.reply_text(
            f"Your Current Metadata:\n\n➜ `{user_metadata}`",
            reply_markup=InlineKeyboardMarkup(ON)
        )
    else:
        await message.reply_text(
            f"Your Current Metadata:\n\n➜ `{user_metadata}`",
            reply_markup=InlineKeyboardMarkup(OFF)
        )


@Client.on_callback_query(filters.regex('.*?(custom_metadata|metadata).*?'))
async def query_metadata(bot: Client, query: CallbackQuery):
    data = query.data
    
    # Handling metadata on/off toggle
    if data.startswith('metadata_'):
        _bool = data.split('_')[1]
        user_metadata = await db.get_metadata_code(query.from_user.id)
        
        if _bool == '1':
            # Toggle metadata off
            await db.set_metadata(query.from_user.id, bool_meta=False)
            await query.message.edit(
                f"Your Current Metadata:\n\n➜ `{user_metadata}`",
                reply_markup=InlineKeyboardMarkup(OFF)
            )
        else:
            # Toggle metadata on
            await db.set_metadata(query.from_user.id, bool_meta=True)
            await query.message.edit(
                f"Your Current Metadata:\n\n➜ `{user_metadata}`",
                reply_markup=InlineKeyboardMarkup(ON)
            )

    elif data == 'custom_metadata':
        # Handle custom metadata input
        await query.message.delete()  # Delete the original message
        
        try:
            metadata = await bot.ask(
                text=Txt.SEND_METADATA, 
                chat_id=query.from_user.id, 
                filters=filters.text,
                timeout=30,  # 30 seconds to respond
                disable_web_page_preview=True
            )
            
            ms = await query.message.reply_text("**Please Wait...**", reply_to_message_id=metadata.id)
            
            # Store the custom metadata
            await db.set_metadata_code(query.from_user.id, metadata.text)
            
            await ms.edit("**Your Metadata Code Set Successfully ✅**")
        
        except ListenerTimeout:
            await query.message.reply_text(
                "⚠️ Error!\n\n**Request timed out.**\nRestart by using /metadata",
                reply_to_message_id=query.message.id
            )
        except Exception as e:
            # Log or print the exception for debugging purposes
            print(f"An error occurred: {e}")
            await query.message.reply_text(
                "⚠️ An error occurred while setting metadata. Please try again.",
                reply_to_message_id=query.message.id
            )
            
