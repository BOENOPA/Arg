import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

PURPLE = discord.Color.from_rgb(115, 55, 210)

# Estado personalizado que activa el rol
VANITY_TEXT = "?"


# ============================================================
# COG
# ============================================================

class Vanity(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.data = self.bot.load_cog_data("vanity")

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", flush=True)
        print("[VANITY] Cog iniciado", flush=True)
        print(f"[VANITY] Estado requerido: {VANITY_TEXT}", flush=True)
        print(f"[VANITY] Datos cargados: {self.data}", flush=True)
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", flush=True)

    # ========================================================
    # GUARDAR DATOS
    # ========================================================

    def save(self):
        self.bot.save_cog_data("vanity", self.data)

    # ========================================================
    # OBTENER ESTADO PERSONALIZADO
    # ========================================================

    def get_custom_status(self, member: discord.Member):

        print(
            f"[VANITY] Revisando estado personalizado de "
            f"{member} ({member.id})",
            flush=True
        )

        for activity in member.activities:

            print(
                f"[VANITY] Actividad detectada: "
                f"{type(activity).__name__} | "
                f"name={getattr(activity, 'name', None)!r} | "
                f"state={getattr(activity, 'state', None)!r}",
                flush=True
            )

            if isinstance(activity, discord.CustomActivity):

                status = activity.name or activity.state or ""

                print(
                    f"[VANITY] Custom Status de {member}: "
                    f"{status!r}",
                    flush=True
                )

                return status

        print(
            f"[VANITY] {member} no tiene Custom Status",
            flush=True
        )

        return ""

    # ========================================================
    # DETECTAR SERVER TAG
    # ========================================================

    def get_server_tag_info(self, member: discord.Member):

        print(
            f"[VANITY TAG] Revisando Server Tag de "
            f"{member} ({member.id})",
            flush=True
        )

        try:
            primary_guild = member.primary_guild

            print(
                f"[VANITY TAG] primary_guild = "
                f"{primary_guild!r}",
                flush=True
            )

        except Exception as error:

            print(
                f"[VANITY TAG] ERROR obteniendo primary_guild "
                f"de {member}: {error}",
                flush=True
            )

            return False, None

        if primary_guild is None:

            print(
                f"[VANITY TAG] ❌ {member} NO tiene Server Tag",
                flush=True
            )

            return False, None

        identity_guild_id = getattr(
            primary_guild,
            "identity_guild_id",
            None
        )

        identity_enabled = getattr(
            primary_guild,
            "identity_enabled",
            None
        )

        tag = getattr(
            primary_guild,
            "tag",
            None
        )

        badge = getattr(
            primary_guild,
            "badge",
            None
        )

        print(
            "[VANITY TAG] Información detectada:",
            flush=True
        )

        print(
            f"[VANITY TAG]   identity_guild_id = "
            f"{identity_guild_id}",
            flush=True
        )

        print(
            f"[VANITY TAG]   guild actual = "
            f"{member.guild.id}",
            flush=True
        )

        print(
            f"[VANITY TAG]   identity_enabled = "
            f"{identity_enabled}",
            flush=True
        )

        print(
            f"[VANITY TAG]   tag = "
            f"{tag!r}",
            flush=True
        )

        print(
            f"[VANITY TAG]   badge = "
            f"{badge!r}",
            flush=True
        )

        if identity_guild_id != member.guild.id:

            print(
                f"[VANITY TAG] ❌ El Server Tag pertenece "
                f"a otro servidor",
                flush=True
            )

            return False, tag

        if identity_enabled is not True:

            print(
                f"[VANITY TAG] ❌ identity_enabled no está activo",
                flush=True
            )

            return False, tag

        if not tag:

            print(
                f"[VANITY TAG] ❌ Discord no entregó el texto del Tag",
                flush=True
            )

            return False, tag

        print(
            f"[VANITY TAG] ✅ SERVER TAG DETECTADO: {tag!r}",
            flush=True
        )

        return True, tag

    # ========================================================
    # COMPROBAR SI TIENE VANITY
    # ========================================================

    async def update_member(self, member: discord.Member):

        if member.bot:
            return

        guild_id = str(member.guild.id)

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", flush=True)

        print(
            f"[VANITY] Actualizando miembro: "
            f"{member} ({member.id})",
            flush=True
        )

        print(
            f"[VANITY] Servidor: "
            f"{member.guild.name} ({member.guild.id})",
            flush=True
        )

        config = self.data.get(guild_id)

        if not config:

            print(
                f"[VANITY] ❌ No hay configuración para "
                f"el servidor {member.guild.id}",
                flush=True
            )

            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", flush=True)

            return

        role_id = config.get("role_id")

        if not role_id:

            print(
                "[VANITY] ❌ No hay role_id configurado",
                flush=True
            )

            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", flush=True)

            return

        role = member.guild.get_role(int(role_id))

        if role is None:

            print(
                f"[VANITY] ❌ No se encontró el rol "
                f"{role_id}",
                flush=True
            )

            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", flush=True)

            return

        # ----------------------------------------------------
        # CUSTOM STATUS
        # ----------------------------------------------------

        status = self.get_custom_status(member)

        tiene_estado = VANITY_TEXT.lower() in status.lower()

        print(
            f"[VANITY] ¿Tiene '{VANITY_TEXT}' en estado?: "
            f"{tiene_estado}",
            flush=True
        )

        # ----------------------------------------------------
        # SERVER TAG
        # ----------------------------------------------------

        tiene_tag, tag = self.get_server_tag_info(member)

        print(
            f"[VANITY] ¿Tiene Server Tag?: "
            f"{tiene_tag}",
            flush=True
        )

        # ----------------------------------------------------
        # RESULTADO FINAL
        # ----------------------------------------------------

        tiene_vanity = tiene_estado or tiene_tag

        print(
            f"[VANITY] RESULTADO FINAL: "
            f"tiene_vanity={tiene_vanity}",
            flush=True
        )

        # ----------------------------------------------------
        # DAR ROL
        # ----------------------------------------------------

        if tiene_vanity:

            if role not in member.roles:

                try:

                    await member.add_roles(
                        role,
                        reason="Vanity / Server Tag detectado"
                    )

                    print(
                        f"[VANITY] ✅ Rol '{role.name}' "
                        f"agregado a {member}",
                        flush=True
                    )

                except discord.Forbidden:

                    print(
                        f"[VANITY] ❌ Discord rechazó agregar "
                        f"el rol '{role.name}'",
                        flush=True
                    )

                except discord.HTTPException as error:

                    print(
                        f"[VANITY] ❌ Error HTTP agregando rol: "
                        f"{error}",
                        flush=True
                    )

            else:

                print(
                    f"[VANITY] ℹ️ {member} ya tiene "
                    f"el rol '{role.name}'",
                    flush=True
                )

        # ----------------------------------------------------
        # QUITAR ROL
        # ----------------------------------------------------

        else:

            if role in member.roles:

                try:

                    await member.remove_roles(
                        role,
                        reason="Vanity / Server Tag ya no detectado"
                    )

                    print(
                        f"[VANITY] ❌ Rol '{role.name}' "
                        f"quitado a {member}",
                        flush=True
                    )

                except discord.Forbidden:

                    print(
                        f"[VANITY] ❌ Discord rechazó quitar "
                        f"el rol '{role.name}'",
                        flush=True
                    )

                except discord.HTTPException as error:

                    print(
                        f"[VANITY] ❌ Error HTTP quitando rol: "
                        f"{error}",
                        flush=True
                    )

            else:

                print(
                    f"[VANITY] ℹ️ {member} no tiene "
                    f"el rol '{role.name}'",
                    flush=True
                )

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", flush=True)

    # ========================================================
    # PRESENCE UPDATE
    # ========================================================

    @commands.Cog.listener()
    async def on_presence_update(
        self,
        before: discord.Member,
        after: discord.Member
    ):

        print(
            f"[VANITY EVENT] on_presence_update -> "
            f"{after} ({after.id})",
            flush=True
        )

        before_status = self.get_custom_status(before)
        after_status = self.get_custom_status(after)

        print(
            f"[VANITY EVENT] Estado anterior: "
            f"{before_status!r}",
            flush=True
        )

        print(
            f"[VANITY EVENT] Estado nuevo: "
            f"{after_status!r}",
            flush=True
        )

        if before_status != after_status:

            print(
                "[VANITY EVENT] ⚡ Cambio de Custom Status detectado",
                flush=True
            )

            await self.update_member(after)

    # ========================================================
    # MEMBER UPDATE
    # ========================================================

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member
    ):

        print(
            f"[VANITY EVENT] on_member_update -> "
            f"{after} ({after.id})",
            flush=True
        )

        try:

            before_primary = before.primary_guild
            after_primary = after.primary_guild

            print(
                f"[VANITY EVENT] BEFORE primary_guild: "
                f"{before_primary!r}",
                flush=True
            )

            print(
                f"[VANITY EVENT] AFTER primary_guild: "
                f"{after_primary!r}",
                flush=True
            )

            before_tag = getattr(
                before_primary,
                "tag",
                None
            )

            after_tag = getattr(
                after_primary,
                "tag",
                None
            )

            before_enabled = getattr(
                before_primary,
                "identity_enabled",
                None
            )

            after_enabled = getattr(
                after_primary,
                "identity_enabled",
                None
            )

            print(
                f"[VANITY EVENT] BEFORE tag={before_tag!r} "
                f"enabled={before_enabled}",
                flush=True
            )

            print(
                f"[VANITY EVENT] AFTER tag={after_tag!r} "
                f"enabled={after_enabled}",
                flush=True
            )

            if (
                before_tag != after_tag
                or before_enabled != after_enabled
            ):

                print(
                    "[VANITY EVENT] ⚡ Cambio de Server Tag detectado",
                    flush=True
                )

                await self.update_member(after)

        except Exception as error:

            print(
                f"[VANITY EVENT] ❌ Error: {error}",
                flush=True
            )

    # ========================================================
    # GRUPO /VANITY
    # ========================================================

    vanity = app_commands.Group(
        name="vanity",
        description="Configura el sistema de Vanity y Server Tag"
    )

    # ========================================================
    # /vanity agregar
    # ========================================================

    @vanity.command(
        name="agregar",
        description="Configura el rol para Vanity / Server Tag"
    )
    @app_commands.describe(
        rol="Rol que recibirán los miembros"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def agregar(
        self,
        interaction: discord.Interaction,
        rol: discord.Role
    ):

        guild_id = str(interaction.guild.id)

        self.data[guild_id] = {
            "texto": VANITY_TEXT,
            "role_id": rol.id
        }

        self.save()

        embed = discord.Embed(
            title="Vanity configurado",
            description=(
                f"**Estado personalizado:** `{VANITY_TEXT}`\n"
                f"**Server Tag:** automático\n"
                f"**Rol:** {rol.mention}"
            ),
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        print(
            f"[VANITY CONFIG] Servidor {interaction.guild.id} "
            f"configurado | rol={rol.id}",
            flush=True
        )

    # ========================================================
    # /vanity eliminar
    # ========================================================

    @vanity.command(
        name="eliminar",
        description="Elimina la configuración de Vanity"
    )
    @app_commands.describe(
        id="ID del servidor"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def eliminar(
        self,
        interaction: discord.Interaction,
        id: str
    ):

        if id not in self.data:

            await interaction.response.send_message(
                "❌ No existe una configuración para ese servidor.",
                ephemeral=True
            )

            return

        del self.data[id]

        self.save()

        await interaction.response.send_message(
            "✅ Configuración de Vanity eliminada.",
            ephemeral=True
        )

        print(
            f"[VANITY CONFIG] Configuración eliminada "
            f"para servidor {id}",
            flush=True
        )

    # ========================================================
    # /vanity lista
    # ========================================================

    @vanity.command(
        name="lista",
        description="Muestra las configuraciones de Vanity"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def lista(
        self,
        interaction: discord.Interaction
    ):

        if not self.data:

            await interaction.response.send_message(
                "📭 No hay configuraciones de Vanity.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="Configuraciones Vanity",
            color=PURPLE
        )

        for guild_id, config in self.data.items():

            role_id = config.get("role_id")

            guild = self.bot.get_guild(int(guild_id))

            if guild:
                nombre = guild.name
            else:
                nombre = f"Servidor {guild_id}"

            embed.add_field(
                name=nombre,
                value=(
                    f"**ID:** `{guild_id}`\n"
                    f"**Estado:** `{VANITY_TEXT}`\n"
                    f"**Server Tag:** automático\n"
                    f"**Rol:** <@&{role_id}>"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # ========================================================
    # ERRORES
    # ========================================================

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):

        print(
            f"[VANITY ERROR] {type(error).__name__}: {error}",
            flush=True
        )

        if isinstance(
            error,
            app_commands.errors.MissingPermissions
        ):

            mensaje = (
                "❌ Necesitás permisos de **Administrador** "
                "para usar este comando."
            )

        else:

            mensaje = (
                "❌ Ocurrió un error al ejecutar el comando."
            )

        if interaction.response.is_done():

            await interaction.followup.send(
                mensaje,
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                mensaje,
                ephemeral=True
            )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):
    await bot.add_cog(Vanity(bot))

    print(
        "[VANITY] ✅ Cog cargado correctamente",
        flush=True
    )