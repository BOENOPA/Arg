import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta


# ============================================================
# CONFIGURACIÓN VISUAL
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
# COG
# ============================================================

class Moderacion(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        print("========================================")
        print("🛡️ COG MODERACIÓN CARGADO")
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
            f"({interaction.user.id}) intenta mutear a "
            f"{usuario} ({usuario.id}) por {minutos} minutos."
        )

        # ----------------------------------------------------
        # VERIFICAR GUILD
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
        # VERIFICAR PERMISO DEL MODERADOR
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.moderate_members:
            print(
                f"[MUTE] ❌ Sin permisos: "
                f"{interaction.user} ({interaction.user.id})"
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "Necesitás el permiso **Moderar miembros** para utilizar este comando."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # NO MUTear AL MISMO USUARIO
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

        if usuario.id == self.bot.user.id:
            await interaction.response.send_message(
                embed=error_embed(
                    "No podés silenciar al bot."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # COMPROBAR SI EL USUARIO YA ESTÁ MUTED
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
        # COMPROBAR JERARQUÍA
        # ----------------------------------------------------

        if usuario.top_role >= interaction.user.top_role:
            print(
                f"[MUTE] ❌ Jerarquía insuficiente para "
                f"{usuario}."
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "No podés silenciar a un usuario que tiene "
                    "un rol igual o superior al tuyo."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # COMPROBAR BOT
        # ----------------------------------------------------

        bot_member = interaction.guild.me

        if bot_member is None:
            bot_member = interaction.guild.get_member(
                self.bot.user.id
            )

        if bot_member is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "No pude encontrar al bot dentro del servidor."
                ),
                ephemeral=True
            )
            return

        if usuario.top_role >= bot_member.top_role:
            print(
                f"[MUTE] ❌ El bot no puede moderar a "
                f"{usuario} por jerarquía."
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "No puedo silenciar a ese usuario porque su "
                    "rol es igual o superior al mío."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # COMPROBAR MODERABLE
        # ----------------------------------------------------

        if not usuario.moderatable:
            print(
                f"[MUTE] ❌ Usuario no moderable: "
                f"{usuario}"
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "No puedo silenciar a ese usuario. "
                    "Revisá la jerarquía de roles y mis permisos."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # APLICAR TIMEOUT
        # ----------------------------------------------------

        try:

            await usuario.timeout(
                timedelta(minutes=int(minutos)),
                reason=(
                    f"{razon} | "
                    f"Moderador: {interaction.user} "
                    f"({interaction.user.id})"
                )
            )

            print(
                f"[MUTE] ✅ {usuario} fue silenciado "
                f"por {minutos} minutos."
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
                "[MUTE] ❌ Discord rechazó la acción. "
                "Faltan permisos o jerarquía."
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "Discord rechazó la acción. "
                    "Verificá que tenga **Moderar miembros** "
                    "y que mi rol esté por encima del usuario."
                ),
                ephemeral=True
            )

        except discord.HTTPException as e:

            print(
                f"[MUTE] ❌ Error HTTP: {e}"
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "Ocurrió un error de Discord al intentar silenciar al usuario."
                ),
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[MUTE] ❌ Error inesperado: {type(e).__name__}: {e}"
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
        description="Bloquea completamente el canal."
    )
    @app_commands.default_permissions(
        manage_channels=True
    )
    async def lock(
        self,
        interaction: discord.Interaction
    ):

        print(
            f"[LOCK] {interaction.user} "
            f"({interaction.user.id}) ejecutó /lock."
        )

        # ----------------------------------------------------
        # VERIFICAR GUILD
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
        # VERIFICAR PERMISO
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.manage_channels:
            print(
                f"[LOCK] ❌ Sin permisos: "
                f"{interaction.user}"
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "Necesitás el permiso **Administrar canales**."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # OBTENER CANAL
        # ----------------------------------------------------

        canal = interaction.channel

        if not isinstance(
            canal,
            (
                discord.TextChannel,
                discord.Thread,
                discord.VoiceChannel,
                discord.StageChannel
            )
        ):
            await interaction.response.send_message(
                embed=error_embed(
                    "Este canal no admite el sistema de bloqueo."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # BOT
        # ----------------------------------------------------

        me = interaction.guild.me

        if me is None:
            me = interaction.guild.get_member(
                self.bot.user.id
            )

        if me is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "No pude encontrar al bot en el servidor."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # VERIFICAR MANAGE CHANNELS DEL BOT
        # ----------------------------------------------------

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
        # RESPONDER ANTES DE HACER MUCHOS CAMBIOS
        # ----------------------------------------------------

        await interaction.response.defer()

        # ----------------------------------------------------
        # BLOQUEAR @EVERYONE
        # ----------------------------------------------------

        try:

            everyone = interaction.guild.default_role

            await canal.set_permissions(
                everyone,
                send_messages=False,
                reason=(
                    f"Lock por {interaction.user} "
                    f"({interaction.user.id})"
                )
            )

            print(
                "[LOCK] ✅ @everyone bloqueado."
            )

        except discord.Forbidden:

            print(
                "[LOCK] ❌ No se pudo modificar @everyone."
            )

            await interaction.followup.send(
                embed=error_embed(
                    "No tengo permisos suficientes para bloquear este canal."
                ),
                ephemeral=True
            )
            return

        except discord.HTTPException as e:

            print(
                f"[LOCK] ❌ Error modificando @everyone: {e}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Discord rechazó la modificación del canal."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # BLOQUEAR TODOS LOS ROLES
        # ----------------------------------------------------

        roles_bloqueados = 0

        for role in interaction.guild.roles:

            # @everyone ya fue bloqueado
            if role.is_default():
                continue

            # No intentar modificar roles superiores al bot
            if role >= me.top_role:
                print(
                    f"[LOCK] ⚠️ No puedo modificar el rol "
                    f"{role.name} por jerarquía."
                )
                continue

            try:

                await canal.set_permissions(
                    role,
                    send_messages=False,
                    reason=(
                        f"Lock por {interaction.user} "
                        f"({interaction.user.id})"
                    )
                )

                roles_bloqueados += 1

                print(
                    f"[LOCK] 🔒 Rol bloqueado: {role.name}"
                )

            except discord.Forbidden:

                print(
                    f"[LOCK] ⚠️ Sin permisos para bloquear: "
                    f"{role.name}"
                )

            except discord.HTTPException as e:

                print(
                    f"[LOCK] ⚠️ Error con rol "
                    f"{role.name}: {e}"
                )

        # ----------------------------------------------------
        # PERMITIR AL USUARIO QUE EJECUTÓ /LOCK
        # ----------------------------------------------------

        try:

            await canal.set_permissions(
                interaction.user,
                send_messages=True,
                reason=(
                    f"Excepción de lock para "
                    f"{interaction.user}"
                )
            )

            print(
                f"[LOCK] ✅ Excepción permitida: "
                f"{interaction.user}"
            )

        except discord.Forbidden:

            print(
                "[LOCK] ⚠️ No pude crear la excepción para "
                "el moderador."
            )

        # ----------------------------------------------------
        # PERMITIR AL BOT
        # ----------------------------------------------------

        try:

            await canal.set_permissions(
                me,
                send_messages=True,
                reason="Permitir al bot escribir durante el lock"
            )

            print(
                "[LOCK] ✅ Bot permitido."
            )

        except discord.Forbidden:

            print(
                "[LOCK] ⚠️ No pude permitir al bot."
            )

        # ----------------------------------------------------
        # MENSAJE
        # ----------------------------------------------------

        embed = success_embed(
            "🔒 Canal bloqueado",
            (
                f"Este canal fue bloqueado por "
                f"{interaction.user.mention}.\n\n"
                f"👤 **Excepción:** {interaction.user.mention}\n"
                f"🤖 **Bot:** permitido\n"
                f"🔒 **Roles bloqueados:** `{roles_bloqueados}`"
            )
        )

        await interaction.followup.send(
            embed=embed
        )

        print(
            f"[LOCK] ✅ Canal #{canal.name} bloqueado correctamente."
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
            f"[UNLOCK] {interaction.user} "
            f"({interaction.user.id}) ejecutó /unlock."
        )

        # ----------------------------------------------------
        # VERIFICAR GUILD
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
        # VERIFICAR PERMISO
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.manage_channels:
            print(
                f"[UNLOCK] ❌ Sin permisos: "
                f"{interaction.user}"
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "Necesitás el permiso **Administrar canales**."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # OBTENER CANAL
        # ----------------------------------------------------

        canal = interaction.channel

        if not isinstance(
            canal,
            (
                discord.TextChannel,
                discord.Thread,
                discord.VoiceChannel,
                discord.StageChannel
            )
        ):
            await interaction.response.send_message(
                embed=error_embed(
                    "Este canal no admite el sistema de desbloqueo."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # BOT
        # ----------------------------------------------------

        me = interaction.guild.me

        if me is None:
            me = interaction.guild.get_member(
                self.bot.user.id
            )

        # ----------------------------------------------------
        # RESPONDER ANTES
        # ----------------------------------------------------

        await interaction.response.defer()

        # ----------------------------------------------------
        # DESBLOQUEAR @EVERYONE
        # ----------------------------------------------------

        everyone = interaction.guild.default_role

        try:

            await canal.set_permissions(
                everyone,
                send_messages=None,
                reason=(
                    f"Unlock por {interaction.user} "
                    f"({interaction.user.id})"
                )
            )

            print(
                "[UNLOCK] ✅ @everyone restaurado."
            )

        except discord.Forbidden:

            print(
                "[UNLOCK] ❌ No se pudo modificar @everyone."
            )

            await interaction.followup.send(
                embed=error_embed(
                    "No tengo permisos suficientes para desbloquear este canal."
                ),
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # DESBLOQUEAR ROLES
        # ----------------------------------------------------

        roles_restaurados = 0

        for role in interaction.guild.roles:

            if role.is_default():
                continue

            if me is not None and role >= me.top_role:
                print(
                    f"[UNLOCK] ⚠️ No puedo modificar el rol "
                    f"{role.name} por jerarquía."
                )
                continue

            try:

                await canal.set_permissions(
                    role,
                    send_messages=None,
                    reason=(
                        f"Unlock por {interaction.user} "
                        f"({interaction.user.id})"
                    )
                )

                roles_restaurados += 1

                print(
                    f"[UNLOCK] 🔓 Rol restaurado: "
                    f"{role.name}"
                )

            except discord.Forbidden:

                print(
                    f"[UNLOCK] ⚠️ Sin permisos para restaurar: "
                    f"{role.name}"
                )

            except discord.HTTPException as e:

                print(
                    f"[UNLOCK] ⚠️ Error con rol "
                    f"{role.name}: {e}"
                )

        # ----------------------------------------------------
        # QUITAR EXCEPCIONES INDIVIDUALES DEL LOCK
        # ----------------------------------------------------

        try:

            await canal.set_permissions(
                interaction.user,
                send_messages=None,
                reason="Eliminar excepción individual del lock"
            )

            print(
                f"[UNLOCK] ✅ Excepción eliminada: "
                f"{interaction.user}"
            )

        except discord.Forbidden:

            print(
                "[UNLOCK] ⚠️ No pude eliminar la excepción del moderador."
            )

        # ----------------------------------------------------
        # QUITAR EXCEPCIÓN DEL BOT
        # ----------------------------------------------------

        if me is not None:

            try:

                await canal.set_permissions(
                    me,
                    send_messages=None,
                    reason="Eliminar excepción del bot"
                )

                print(
                    "[UNLOCK] ✅ Excepción del bot eliminada."
                )

            except discord.Forbidden:

                print(
                    "[UNLOCK] ⚠️ No pude eliminar la excepción del bot."
                )

        # ----------------------------------------------------
        # MENSAJE
        # ----------------------------------------------------

        embed = success_embed(
            "🔓 Canal desbloqueado",
            (
                f"Este canal fue desbloqueado por "
                f"{interaction.user.mention}.\n\n"
                f"💬 Los permisos de escritura fueron "
                f"restaurados a su estado normal."
            )
        )

        await interaction.followup.send(
            embed=embed
        )

        print(
            f"[UNLOCK] ✅ Canal #{canal.name} desbloqueado correctamente."
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