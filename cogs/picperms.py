
import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

ROLE_ID = 1548804942330986608
CHANNEL_NAME = "pic-perms"

PURPLE = discord.Color.from_rgb(115, 55, 210)


# ============================================================
# BOTÓN PARA RECLAMAR EL ROL
# ============================================================

class PicPermsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Reclamar Pic Perms",
        style=discord.ButtonStyle.primary,
        emoji="📸",
        custom_id="picperms:claim"
    )
    async def claim_role(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "❌ Este botón solo funciona dentro de un servidor.",
                ephemeral=True
            )
            return

        role = guild.get_role(ROLE_ID)

        if role is None:
            await interaction.response.send_message(
                "❌ No encontré el rol configurado.",
                ephemeral=True
            )
            return

        member = interaction.user

        if role in member.roles:
            await interaction.response.send_message(
                "⚠️ Ya tenés el rol de Pic Perms.",
                ephemeral=True
            )
            return

        if not guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "❌ No tengo permiso para administrar roles.",
                ephemeral=True
            )
            return

        if role >= guild.me.top_role:
            await interaction.response.send_message(
                "❌ No puedo entregar este rol porque está "
                "por encima de mi rol más alto.",
                ephemeral=True
            )
            return

        try:
            await member.add_roles(
                role,
                reason="Reclamó el rol de Pic Perms"
            )

            embed = discord.Embed(
                title="¡Rol reclamado!",
                description=(
                    f"🎉 Se te asignó correctamente el rol "
                    f"{role.mention}.\n\n"
                    "Ahora podés disfrutar de sus beneficios."
                ),
                color=PURPLE
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ No tengo permisos para asignarte ese rol.",
                ephemeral=True
            )

        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Ocurrió un error al asignar el rol.",
                ephemeral=True
            )


# ============================================================
# COG
# ============================================================

class PicPerms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="picperms",
        description="Crea el canal para reclamar Pic Perms."
    )
    @app_commands.default_permissions(manage_channels=True)
    async def picperms(self, interaction: discord.Interaction):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo funciona en un servidor.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Comprobar si el canal ya existe
        existing_channel = discord.utils.get(
            guild.text_channels,
            name=CHANNEL_NAME
        )

        if existing_channel:
            await interaction.followup.send(
                f"⚠️ El canal ya existe: {existing_channel.mention}",
                ephemeral=True
            )
            return

        # Comprobar permisos del bot
        if not guild.me.guild_permissions.manage_channels:
            await interaction.followup.send(
                "❌ Necesito el permiso Administrar canales.",
                ephemeral=True
            )
            return

        # Crear el canal
        channel = await guild.create_text_channel(
            CHANNEL_NAME,
            reason="Creación del canal de Pic Perms"
        )

        # Crear el panel
        embed = discord.Embed(
            title="📸 PIC PERMS",
            description=(
                "¿Querés acceder a los Pic Perms?\n\n"
                "Presioná el botón de abajo para reclamar "
                "tu rol automáticamente.\n\n"
                "・El rol se asigna una sola vez.\n"
                "・No necesitás contactar a ningún staff.\n"
                "・Respetá las reglas del servidor."
            ),
            color=PURPLE
        )

        embed.set_footer(
            text="Sistema de Pic Perms • 67"
        )

        await channel.send(
            embed=embed,
            view=PicPermsView()
        )

        await interaction.followup.send(
            f"✅ Canal creado correctamente: {channel.mention}",
            ephemeral=True
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):
    await bot.add_cog(PicPerms(bot))
