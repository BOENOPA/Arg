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
    f"୨୧・₊˚ **¡HOLAAA, BIENVENIDO/A!** ˚₊・୨୧\n\n"
    f"🌷 {usuario.mention} **se acaba de sumar a la bandita** 💗\n\n"
    f"🧸 Ponete cómodo/a, este rinconcito ahora también es tuyo.\n"
    f"🧉 Agarrá unos mates, conocé gente y pasala lindo.\n"
    f"✨ Esperamos que te sientas como en casa.\n\n"
    f"୨୧・₊˚ **¡Qué lindo tenerte acá!** 💕 ˚₊・୨୧"
)

await respuesta.add_reaction("💗")
await respuesta.add_reaction("🧸")
await respuesta.add_reaction("🇦🇷")