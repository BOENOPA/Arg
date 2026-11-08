
import discord
from discord.ext import commands
from discord import app_commands


class InvitarBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="invitar_bot",
        description="Genera el enlace para invitar al bot a otro servidor."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def invitar_bot(self, interaction: discord.Interaction):

        client_id = self.bot.user.id

        permissions = discord.Permissions(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True,
            manage_roles=True,
            manage_messages=True,
            embed_links=True,
            attach_files=True,
            add_reactions=True
        )

        url = discord.utils.oauth_url(
            client_id,
            permissions=permissions,
            scopes=("bot", "applications.commands")
        )

        embed = discord.Embed(
            title="🤖 INVITAR BOT",
            description=(
                "¡Querés agregarme a otro servidor?\n\n"
                f"**[➕ INVITAR BOT]({url})**\n\n"
                "Presioná el enlace para autorizarme."
            ),
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="Sistema de invitaciones"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(InvitarBot(bot))
