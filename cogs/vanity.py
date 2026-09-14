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
# COG VANITY
# ============================================================
class Vanity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Usa el sistema de datos de tu bot.py
        self.data = self.bot.load_cog_data("vanity")
    # ========================================================
    # GUARDAR DATOS
    # ========================================================
    def save(self):
        self.bot.save_cog_data("vanity", self.data)
    # ========================================================
    # OBTENER CUSTOM STATUS
    # ========================================================
    def get_custom_status(self, member: discord.Member):
        for activity in member.activities:
            if isinstance(activity, discord.CustomActivity):
                if activity.name:
                    return str(activity.name).strip()
                if activity.state:
                    return str(activity.state).strip()
        return ""
    # ========================================================
    # COMPROBAR SERVER TAG
    # ========================================================
    def has_server_tag(self, member: discord.Member) -> bool:
        try:
            primary_guild = member.primary_guild
            if primary_guild is None:
                return False
            # La etiqueta pertenece a este servidor
            if primary_guild.identity_guild_id != member.guild.id:
                return False
            # El usuario está mostrando la etiqueta
            if primary_guild.identity_enabled is not True:
                return False
            # La etiqueta existe
            if not primary_guild.tag:
                return False
            return True
        except (AttributeError, TypeError):
            return False
    # ========================================================
    # ACTUALIZAR ROLES
    # ========================================================
    async def update_member(self, member: discord.Member):
        guild_id = str(member.guild.id)
        guild_data = self.data.get(guild_id, {})
        if not guild_data:
            return
        status = self.get_custom_status(member).lower()
        tiene_estado = VANITY_TEXT.lower() in status
        tiene_tag = self.has_server_tag(member)
        # Cualquiera de los dos sirve
        tiene_vanity = tiene_estado or tiene_tag
        for vanity_id, config in list(guild_data.items()):
            role_id = config.get("role_id")
            if not role_id:
                continue
            try:
                role = member.guild.get_role(int(role_id))
            except (ValueError, TypeError):
                continue
            if role is None:
                continue
            # =================================================
            # TIENE ESTADO O SERVER TAG
            # =================================================
            if tiene_vanity:
                if role not in member.roles:
                    try:
                        await member.add_roles(
                            role,
                            reason="Vanity Role detectado"
                        )
                        motivo = []
                        if tiene_estado:
                            motivo.append("estado ?")
                        if tiene_tag:
                            motivo.append("Server Tag")
                        print(
                            f"🎨 VANITY | "
                            f"+{role.name} | "
                            f"{member} | "
                            f"{' + '.join(motivo)}",
                            flush=True
                        )
                    except discord.Forbidden:
                        print(
                            f"❌ VANITY | "
                            f"No puedo dar {role.name} "
                            f"a {member}",
                            flush=True
                        )
                    except discord.HTTPException as error:
                        print(
                            f"❌ VANITY | Error Discord: "
                            f"{error}",
                            flush=True
                        )
            # =================================================
            # NO TIENE NI ESTADO NI SERVER TAG
            # =================================================
            else:
                if role in member.roles:
                    try:
                        await member.remove_roles(
                            role,
                            reason="Vanity Role eliminado"
                        )
                        print(
                            f"🎨 VANITY | "
                            f"-{role.name} | "
                            f"{member}",
                            flush=True
                        )
                    except discord.Forbidden:
                        print(
                            f"❌ VANITY | "
                            f"No puedo quitar {role.name} "
                            f"a {member}",
                            flush=True
                        )
                    except discord.HTTPException as error:
                        print(
                            f"❌ VANITY | Error Discord: "
                            f"{error}",
                            flush=True
                        )
    # ========================================================
    # DETECTAR CAMBIOS DE PRESENCIA
    # ========================================================
    @commands.Cog.listener()
    async def on_presence_update(
        self,
        before: discord.Member,
        after: discord.Member
    ):
        before_status = self.get_custom_status(before)
        after_status = self.get_custom_status(after)
        # Si el estado no cambió, no hacemos nada
        if before_status == after_status:
            return
        await self.update_member(after)
    # ========================================================
    # DETECTAR CAMBIOS DE SERVER TAG
    # ========================================================
    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member
    ):
        try:
            before_guild = before.primary_guild
            after_guild = after.primary_guild
            before_tag = (
                before_guild.identity_guild_id == before.guild.id
                and before_guild.identity_enabled is True
                if before_guild
                else False
            )
            after_tag = (
                after_guild.identity_guild_id == after.guild.id
                and after_guild.identity_enabled is True
                if after_guild
                else False
            )
            # Si la etiqueta no cambió, ignorar
            if before_tag == after_tag:
                return
        except (AttributeError, TypeError):
            return
        await self.update_member(after)
    # ========================================================
    # GRUPO /VANITY
    # ========================================================
    vanity = app_commands.Group(
        name="vanity",
        description="Sistema de Vanity Roles."
    )
    # ========================================================
    # /VANITY AGREGAR
    # ========================================================
    @vanity.command(
        name="agregar",
        description="Configura un Vanity Role."
    )
    @app_commands.describe(
        rol="Rol que recibirá automáticamente."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def agregar(
        self,
        interaction: discord.Interaction,
        rol: discord.Role
    ):
        # ====================================================
        # COMPROBAR SERVIDOR
        # ====================================================
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse "
                "dentro de un servidor.",
                ephemeral=True
            )
            return
        # ====================================================
        # COMPROBAR JERARQUÍA DEL BOT
        # ====================================================
        bot_member = interaction.guild.me
        if bot_member is None:
            await interaction.response.send_message(
                "❌ No pude comprobar mi rol.",
                ephemeral=True
            )
            return
        if rol >= bot_member.top_role:
            await interaction.response.send_message(
                "❌ No puedo administrar ese rol.\n\n"
                "Mi rol debe estar **por encima** "
                "del rol Vanity.",
                ephemeral=True
            )
            return
        # ====================================================
        # CREAR CONFIG DEL SERVIDOR
        # ====================================================
        guild_id = str(interaction.guild.id)
        if guild_id not in self.data:
            self.data[guild_id] = {}
        # ====================================================
        # EVITAR DUPLICADOS
        # ====================================================
        for config in self.data[guild_id].values():
            if (
                config.get("texto", "").lower()
                == VANITY_TEXT.lower()
            ):
                await interaction.response.send_message(
                    "❌ El Vanity "
                    f"`{VANITY_TEXT}` ya está configurado.",
                    ephemeral=True
                )
                return
        # ====================================================
        # GENERAR ID
        # ====================================================
        existing_ids = []
        for key in self.data[guild_id].keys():
            try:
                existing_ids.append(int(key))
            except (ValueError, TypeError):
                pass
        if existing_ids:
            vanity_id = str(max(existing_ids) + 1)
        else:
            vanity_id = "1"
        # ====================================================
        # GUARDAR
        # ====================================================
        self.data[guild_id][vanity_id] = {
            "texto": VANITY_TEXT,
            "role_id": str(rol.id)
        }
        self.save()
        # ====================================================
        # EMBED
        # ====================================================
        embed = discord.Embed(
            title="✦ Vanity Role configurado",
            description=(
                "El sistema ya está activo.\n\n"
                f"Cuando una persona coloque `{VANITY_TEXT}` "
                "en su **estado personalizado** "
                "o tenga la **Server Tag de este servidor**, "
                "recibirá automáticamente el rol."
            ),
            color=PURPLE
        )
        embed.add_field(
            name="Estado personalizado",
            value=f"`{VANITY_TEXT}`",
            inline=True
        )
        embed.add_field(
            name="Server Tag",
            value="Activada automáticamente",
            inline=True
        )
        embed.add_field(
            name="Rol",
            value=rol.mention,
            inline=False
        )
        embed.add_field(
            name="ID",
            value=f"`{vanity_id}`",
            inline=True
        )
        await interaction.response.send_message(
            embed=embed
        )
    # ========================================================
    # /VANITY ELIMINAR
    # ========================================================
    @vanity.command(
        name="eliminar",
        description="Elimina un Vanity Role."
    )
    @app_commands.describe(
        id="ID del Vanity que querés eliminar."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def eliminar(
        self,
        interaction: discord.Interaction,
        id: str
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse "
                "dentro de un servidor.",
                ephemeral=True
            )
            return
        guild_id = str(interaction.guild.id)
        guild_data = self.data.get(
            guild_id,
            {}
        )
        if id not in guild_data:
            await interaction.response.send_message(
                "❌ No existe un Vanity con ese ID.",
                ephemeral=True
            )
            return
        config = guild_data[id]
        texto = config.get(
            "texto",
            VANITY_TEXT
        )
        del guild_data[id]
        self.save()
        await interaction.response.send_message(
            f"🗑️ Vanity `{texto}` eliminado.",
            ephemeral=True
        )
    # ========================================================
    # /VANITY LISTA
    # ========================================================
    @vanity.command(
        name="lista",
        description="Muestra los Vanity configurados."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def lista(
        self,
        interaction: discord.Interaction
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse "
                "dentro de un servidor.",
                ephemeral=True
            )
            return
        guild_id = str(interaction.guild.id)
        guild_data = self.data.get(
            guild_id,
            {}
        )
        if not guild_data:
            await interaction.response.send_message(
                "📭 No hay Vanity Roles configurados.",
                ephemeral=True
            )
            return
        lines = []
        for vanity_id, config in guild_data.items():
            texto = config.get(
                "texto",
                VANITY_TEXT
            )
            role_id = config.get("role_id")
            try:
                role = interaction.guild.get_role(
                    int(role_id)
                )
            except (ValueError, TypeError):
                role = None
            if role:
                role_text = role.mention
            else:
                role_text = "❌ Rol eliminado"
            lines.append(
                f"**`{vanity_id}`** "
                f"`{texto}` → {role_text}"
            )
        embed = discord.Embed(
            title="✦ Vanity Roles",
            description="\n".join(lines),
            color=PURPLE
        )
        embed.set_footer(
            text="Estado ? + Server Tag"
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
    # ========================================================
    # MANEJO DE ERRORES
    # ========================================================
    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        if isinstance(
            error,
            app_commands.MissingPermissions
        ):
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Necesitás el permiso "
                    "**Gestionar servidor**.",
                    ephemeral=True
                )
            return
        if interaction.response.is_done():
            return
        await interaction.response.send_message(
            "❌ Ocurrió un error al ejecutar "
            "el comando.",
            ephemeral=True
        )
        print(
            f"❌ Error Vanity: "
            f"{type(error).__name__}: {error}",
            flush=True
        )
# ============================================================
# SETUP
# ============================================================
async def setup(bot):
    await bot.add_cog(
        Vanity(bot)
    )