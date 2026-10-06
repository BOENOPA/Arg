import discord
from discord.ext import commands


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):

        # Ignorar mensajes del bot
        if message.author.bot:
            return

        # Solo activar con "wlc"
        if message.content.lower().strip() != "wlc":
            return

        # Comprobar que sea una respuesta
        if not message.reference:
            return

        try:
            mensaje_original = await message.channel.fetch_message(
                message.reference.message_id
            )
        except discord.NotFound:
            return

        usuario = mensaje_original.author

        # Mensaje de bienvenida
        respuesta = await message.channel.send(
            f"🎉 **¡Bienvenido/a al servidor, {usuario.mention}!** 🎉\n"
            f"👋 ¡Qué bueno tenerte acá!\n"
            f"❤️ Esperamos que la pases genial."
        )

        # Reacciones
        await respuesta.add_reaction("👋")
        await respuesta.add_reaction("❤️")
        await respuesta.add_reaction("🎉")


async def setup(bot):
    await bot.add_cog(Welcome(bot))