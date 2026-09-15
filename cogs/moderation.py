import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta


# ============================================================
# CONFIGURACIÓN
# ============================================================

PURPLE = discord.Color.from_rgb(115, 55, 210)
RED = discord.Color.from_rgb(220, 60, 70)
GREEN = discord.Color.from_rgb(45, 190, 110)


# ============================================================
# EMBEDS
# ============================================================

def error_embed(text: str):
    return discord.Embed(
        description=f"❌ {text}",
        color=RED
    )


def success_embed(title: str, description: str):
    return discord.Embed(
        title=title,
        description=description,
        color=PURPLE
    )


# ============================================================
# COG MODERACIÓN
# ============================================================

class Moderacion(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        print("========================================")
        print("🛡️ MODERACIÓN")
        print("✅ Cog cargado correctamente")
        print("========================================")


    # ========================================================
    # MUTE
    # ========================================================

    @app_commands.command(
        name="mute",
        description="Silencia temporalmente a un usuario."
    )
    @app_commands.describe(
        usuario="Usuario que querés silenciar",
        minutos="Duración del mute en minutos",
        razon="Razón del mute"
    )
    @app_commands.default_permissions(
        moderate_members=True
    )
    async def mute(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        minutos: app_commands.Range[int, 1, 40320],
        razon: str = "Sin razón especificada"
    ):

        print(
            f"[MUTE] {interaction.user} "
            f"-> {usuario} | {minutos} minutos"
        )

        if interaction.guild is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente puede utilizarse dentro de un servidor."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # PERMISOS DEL MODERADOR
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.moderate_members:
            print("[MUTE] ❌ El usuario no tiene permisos.")

            await interaction.response.send_message(
                embed=error_embed(
                    "Necesitás el permiso **Moderar miembros**."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # NO MUTearSE
        # ----------------------------------------------------

        if usuario.id == interaction.user.id:
            await interaction.response.send_message(
                embed=error_embed(
                    "No podés silenciarte a vos mismo."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # NO MUTear AL BOT
        # ----------------------------------------------------

        if self.bot.user and usuario.id == self.bot.user.id:
            await interaction.response.send_message(
                embed=error_embed(
                    "No podés silenciar al bot."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # SI YA ESTÁ MUTED
        # ----------------------------------------------------

        if usuario.is_timed_out():
            await interaction.response.send_message(
                embed=error_embed(
                    f"{usuario.mention} ya está silenciado."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # JERARQUÍA DEL MODERADOR
        # ----------------------------------------------------

        if usuario.top_role >= interaction.user.top_role:
            print("[MUTE] ❌ Jerarquía insuficiente del moderador.")

            await interaction.response.send_message(
                embed=error_embed(
                    "No podés silenciar a un usuario que tiene "
                    "un rol igual o superior al tuyo."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # MIEMBRO DEL BOT
        # ----------------------------------------------------

        me = interaction.guild.me

        if me is None and self.bot.user:
            me = interaction.guild.get_member(
                self.bot.user.id
            )

        if me is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "No pude encontrar al bot dentro del servidor."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # JERARQUÍA DEL BOT
        # ----------------------------------------------------

        if usuario.top_role >= me.top_role:
            print("[MUTE] ❌ El bot está por debajo del usuario.")

            await interaction.response.send_message(
                embed=error_embed(
                    "No puedo silenciar a ese usuario porque su "
                    "rol es igual o superior al mío."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # MODERABLE
        # ----------------------------------------------------

        if not usuario.moderatable:
            print("[MUTE] ❌ Usuario no moderable.")

            await interaction.response.send_message(
                embed=error_embed(
                    "No puedo silenciar a ese usuario. "
                    "Revisá mis permisos y la jerarquía de roles."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # APLICAR MUTE
        # ----------------------------------------------------

        try:

            await usuario.timeout(
                timedelta(minutes=int(minutos)),
                reason=(
                    f"{razon} | "
                    f"Moderador: {interaction.user}"
                )
            )

            print(
                f"[MUTE] ✅ {usuario} silenciado correctamente."
            )

            embed = success_embed(
                "🔇 Usuario silenciado",
                (
                    f"**Usuario:** {usuario.mention}\n"
                    f"**Duración:** `{minutos}` minutos\n"
                    f"**Razón:** {razon}\n"
                    f"**Moderador:** {interaction.user.mention}"
                )
            )

            await interaction.response.send_message(
                embed=embed
            )

        except discord.Forbidden:

            print(
                "[MUTE] ❌ Discord rechazó la acción."
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "No tengo permisos suficientes para silenciar a ese usuario."
                ),
                ephemeral=True
            )

        except discord.HTTPException as e:

            print(
                f"[MUTE] ❌ HTTPException: {e}"
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "Discord rechazó la solicitud."
                ),
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[MUTE] ❌ Error: {type(e).__name__}: {e}"
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "Ocurrió un error inesperado."
                ),
                ephemeral=True
            )


    # ========================================================
    # LOCK
    # ========================================================

    @app_commands.command(
        name="lock",
        description="Bloquea el canal para los usuarios."
    )
    @app_commands.default_permissions(
        manage_channels=True
    )
    async def lock(
        self,
        interaction: discord.Interaction
    ):

        print(
            f"[LOCK] Ejecutado por "
            f"{interaction.user} ({interaction.user.id})"
        )

        # ----------------------------------------------------
        # GUILD
        # ----------------------------------------------------

        if interaction.guild is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente puede utilizarse dentro de un servidor."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # PERMISOS
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.manage_channels:
            print("[LOCK] ❌ Sin Administrar canales.")

            await interaction.response.send_message(
                embed=error_embed(
                    "Necesitás el permiso **Administrar canales**."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # CANAL
        # ----------------------------------------------------

        canal = interaction.channel

        if not isinstance(
            canal,
            discord.TextChannel
        ):
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando debe utilizarse en un canal de texto."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # BOT
        # ----------------------------------------------------

        me = interaction.guild.me

        if me is None and self.bot.user:
            me = interaction.guild.get_member(
                self.bot.user.id
            )

        if me is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "No pude encontrar al bot dentro del servidor."
                ),
                ephemeral=True
            )
            return

        if not me.guild_permissions.manage_channels:
            print(
                "[LOCK] ❌ El bot no tiene Administrar canales."
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "No tengo el permiso **Administrar canales**."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # DEFER
        # ----------------------------------------------------

        await interaction.response.defer()

        everyone = interaction.guild.default_role

        try:

            # =================================================
            # SOLO 3 PETICIONES PRINCIPALES
            # =================================================

            # Bloquear @everyone
            await canal.set_permissions(
                everyone,
                send_messages=False,
                reason=(
                    f"Lock por {interaction.user} "
                    f"({interaction.user.id})"
                )
            )

            print(
                "[LOCK] 🔒 @everyone bloqueado."
            )

            # Permitir al moderador que ejecutó /lock
            await canal.set_permissions(
                interaction.user,
                send_messages=True,
                reason=(
                    f"Excepción de lock para "
                    f"{interaction.user}"
                )
            )

            print(
                f"[LOCK] 👤 Permitido: {interaction.user}"
            )

            # Permitir al bot
            await canal.set_permissions(
                me,
                send_messages=True,
                reason="Permitir al bot durante el lock"
            )

            print(
                "[LOCK] 🤖 Bot permitido."
            )

            # ------------------------------------------------
            # RESPUESTA
            # ------------------------------------------------

            embed = success_embed(
                "🔒 Canal bloqueado",
                (
                    f"El canal fue bloqueado por "
                    f"{interaction.user.mention}.\n\n"
                    f"🔒 **Usuarios:** bloqueados\n"
                    f"👤 **Moderador:** puede escribir\n"
                    f"🤖 **Bot:** puede escribir"
                )
            )

            await interaction.followup.send(
                embed=embed
            )

            print(
                f"[LOCK] ✅ #{canal.name} bloqueado correctamente."
            )

        except discord.Forbidden:

            print(
                "[LOCK] ❌ Discord rechazó una modificación."
            )

            await interaction.followup.send(
                embed=error_embed(
                    "No tengo permisos suficientes para bloquear este canal."
                ),
                ephemeral=True
            )

        except discord.HTTPException as e:

            print(
                f"[LOCK] ❌ HTTPException: {e}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Discord rechazó la modificación del canal."
                ),
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[LOCK] ❌ Error: {type(e).__name__}: {e}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Ocurrió un error inesperado."
                ),
                ephemeral=True
            )


    # ========================================================
    # UNLOCK
    # ========================================================

    @app_commands.command(
        name="unlock",
        description="Desbloquea el canal actual."
    )
    @app_commands.default_permissions(
        manage_channels=True
    )
    async def unlock(
        self,
        interaction: discord.Interaction
    ):

        print(
            f"[UNLOCK] Ejecutado por "
            f"{interaction.user} ({interaction.user.id})"
        )

        # ----------------------------------------------------
        # GUILD
        # ----------------------------------------------------

        if interaction.guild is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente puede utilizarse dentro de un servidor."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # PERMISOS
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.manage_channels:
            print("[UNLOCK] ❌ Sin Administrar canales.")

            await interaction.response.send_message(
                embed=error_embed(
                    "Necesitás el permiso **Administrar canales**."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # CANAL
        # ----------------------------------------------------

        canal = interaction.channel

        if not isinstance(
            canal,
            discord.TextChannel
        ):
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando debe utilizarse en un canal de texto."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # BOT
        # ----------------------------------------------------

        me = interaction.guild.me

        if me is None and self.bot.user:
            me = interaction.guild.get_member(
                self.bot.user.id
            )

        # ----------------------------------------------------
        # DEFER
        # ----------------------------------------------------

        await interaction.response.defer()

        everyone = interaction.guild.default_role

        try:

            # =================================================
            # SOLO 3 PETICIONES PRINCIPALES
            # =================================================

            # Restaurar @everyone
            await canal.set_permissions(
                everyone,
                send_messages=None,
                reason=(
                    f"Unlock por {interaction.user} "
                    f"({interaction.user.id})"
                )
            )

            print(
                "[UNLOCK] 🔓 @everyone restaurado."
            )

            # Quitar excepción del moderador
            await canal.set_permissions(
                interaction.user,
                send_messages=None,
                reason="Eliminar excepción del lock"
            )

            print(
                f"[UNLOCK] 👤 Excepción eliminada: "
                f"{interaction.user}"
            )

            # Quitar excepción del bot
            if me is not None:

                await canal.set_permissions(
                    me,
                    send_messages=None,
                    reason="Eliminar excepción del lock"
                )

                print(
                    "[UNLOCK] 🤖 Excepción del bot eliminada."
                )

            # ------------------------------------------------
            # RESPUESTA
            # ------------------------------------------------

            embed = success_embed(
                "🔓 Canal desbloqueado",
                (
                    f"El canal fue desbloqueado por "
                    f"{interaction.user.mention}.\n\n"
                    f"💬 Los permisos volvieron a su configuración normal."
                )
            )

            await interaction.followup.send(
                embed=embed
            )

            print(
                f"[UNLOCK] ✅ #{canal.name} desbloqueado correctamente."
            )

        except discord.Forbidden:

            print(
                "[UNLOCK] ❌ Discord rechazó una modificación."
            )

            await interaction.followup.send(
                embed=error_embed(
                    "No tengo permisos suficientes para desbloquear este canal."
                ),
                ephemeral=True
            )

        except discord.HTTPException as e:

            print(
                f"[UNLOCK] ❌ HTTPException: {e}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Discord rechazó la modificación del canal."
                ),
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[UNLOCK] ❌ Error: {type(e).__name__}: {e}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Ocurrió un error inesperado."
                ),
                ephemeral=True
            )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    print(
        "🔄 Cargando cogs.moderation..."
    )

    await bot.add_cog(
        Moderacion(bot)
    )

    print(
        "✅ cogs.moderation cargado correctamente."
    )