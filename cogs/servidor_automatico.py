
import discord
from discord.ext import commands
from discord import app_commands
from pathlib import Path
import json

CONFIG_FILE = Path(__file__).with_name("servidor_automatico.json")


def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_config(data):
    CONFIG_FILE.write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )


class TicketPanel(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Abrir ticket",
        emoji="🎫",
        style=discord.ButtonStyle.green,
        custom_id="servidor:abrir_ticket"
    )
    async def abrir(self, interaction, button):
        guild = interaction.guild
        if guild is None:
            return

        existing = discord.utils.get(
            guild.text_channels,
            name=f"ticket-{interaction.user.id}"
        )

        if existing:
            await interaction.response.send_message(
                f"Ya tenés un ticket abierto: {existing.mention}",
                ephemeral=True
            )
            return

        category = discord.utils.get(
            guild.categories,
            name="🎟️ TICKETS"
        )

        if category is None:
            await interaction.response.send_message(
                "No encuentro la categoría de tickets.",
                ephemeral=True
            )
            return

        staff = discord.utils.get(
            guild.roles,
            name="Moderador"
        )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True
            )
        }

        if staff:
            overwrites[staff] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Ticket de soporte",
            description=(
                f"Hola {interaction.user.mention}.\n\n"
                "Explicá tu problema y el equipo de soporte "
                "te atenderá lo antes posible."
            ),
            color=discord.Color.blurple()
        )

        await channel.send(
            content=interaction.user.mention,
            embed=embed,
            view=CloseTicket()
        )

        await interaction.response.send_message(
            f"Tu ticket fue creado: {channel.mention}",
            ephemeral=True
        )


class CloseTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Cerrar ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="servidor:cerrar_ticket"
    )
    async def cerrar(self, interaction, button):
        channel = interaction.channel
        if channel is None:
            return

        if not channel.name.startswith("ticket-"):
            return

        await interaction.response.send_message(
            "🔒 Cerrando ticket..."
        )

        await channel.delete(
            reason=f"Ticket cerrado por {interaction.user}"
        )


class ConfirmarServidor(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.cog = cog

    @discord.ui.button(
        label="Crear servidor",
        style=discord.ButtonStyle.success,
        emoji="🚀"
    )
    async def confirmar(self, interaction, button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "No tenés permiso.",
                ephemeral=True
            )
            return

        await interaction.response.edit_message(
            content="🚀 Organizando el servidor...",
            view=None
        )

        try:
            await self.cog.organizar(interaction.guild)
            await interaction.followup.send(
                "✅ ¡Servidor organizado correctamente!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Me faltan permisos para organizar el servidor. "
                "Revisá mis permisos y la posición de mi rol.",
                ephemeral=True
            )
        except Exception as error:
            await interaction.followup.send(
                f"❌ Ocurrió un error: `{error}`",
                ephemeral=True
            )

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.danger,
        emoji="✖️"
    )
    async def cancelar(self, interaction, button):
        await interaction.response.edit_message(
            content="Operación cancelada.",
            view=None
        )


class ServidorAutomatico(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

        # Vistas persistentes para que funcionen tras reiniciar
        self.bot.add_view(TicketPanel(self))
        self.bot.add_view(CloseTicket())

    async def crear_rol(self, guild, nombre, color, permissions=None):
        role = discord.utils.get(guild.roles, name=nombre)

        if role is None:
            role = await guild.create_role(
                name=nombre,
                color=discord.Color(color),
                permissions=permissions or discord.Permissions.none(),
                reason="Configuración automática"
            )

        return role

    async def crear_categoria(self, guild, nombre, overwrites=None):
        category = discord.utils.get(
            guild.categories,
            name=nombre
        )

        if category is None:
            category = await guild.create_category(
                nombre,
                overwrites=overwrites,
                reason="Configuración automática"
            )

        return category

    async def crear_texto(self, guild, nombre, category):
        channel = discord.utils.get(
            category.text_channels,
            name=nombre
        )

        if channel is None:
            channel = await guild.create_text_channel(
                nombre,
                category=category,
                reason="Configuración automática"
            )

        return channel

    async def crear_voz(self, guild, nombre, category):
        channel = discord.utils.get(
            category.voice_channels,
            name=nombre
        )

        if channel is None:
            channel = await guild.create_voice_channel(
                nombre,
                category=category,
                reason="Configuración automática"
            )

        return channel

    async def organizar(self, guild):
        # ROLES
        admin = await self.crear_rol(
            guild,
            "Administrador",
            0xFF0000,
            discord.Permissions(
                manage_guild=True,
                manage_channels=True,
                manage_roles=True,
                manage_messages=True,
                kick_members=True,
                ban_members=True
            )
        )

        moderator = await self.crear_rol(
            guild,
            "Moderador",
            0x3498DB,
            discord.Permissions(
                manage_messages=True,
                kick_members=True,
                moderate_members=True
            )
        )

        member = await self.crear_rol(
            guild,
            "Comunidad",
            0x2ECC71
        )

        gamer = await self.crear_rol(
            guild,
            "Gamer",
            0x9B59B6
        )

        creative = await self.crear_rol(
            guild,
            "Creativo",
            0xE67E22
        )

        music = await self.crear_rol(
            guild,
            "Música",
            0x1ABC9C
        )

        # CATEGORÍAS
        info = await self.crear_categoria(
            guild,
            "📌 INFORMACIÓN"
        )

        community = await self.crear_categoria(
            guild,
            "💬 COMUNIDAD"
        )

        voice = await self.crear_categoria(
            guild,
            "🔊 VOZ"
        )

        support = await self.crear_categoria(
            guild,
            "🎫 SOPORTE"
        )

        staff_overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            moderator: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            admin: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
        }

        staff_category = await self.crear_categoria(
            guild,
            "🛡️ STAFF",
            staff_overwrites
        )

        ticket_category = await self.crear_categoria(
            guild,
            "🎟️ TICKETS",
            {
                guild.default_role:
                    discord.PermissionOverwrite(view_channel=False),
                moderator:
                    discord.PermissionOverwrite(view_channel=True),
                admin:
                    discord.PermissionOverwrite(view_channel=True)
            }
        )

        # CANALES DE INFORMACIÓN
        rules = await self.crear_texto(
            guild, "📜・reglas", info
        )

        announcements = await self.crear_texto(
            guild, "📢・anuncios", info
        )

        roles_channel = await self.crear_texto(
            guild, "🎭・roles", info
        )

        welcome = await self.crear_texto(
            guild, "👋・bienvenida", info
        )

        # COMUNIDAD
        general = await self.crear_texto(
            guild, "💬・general", community
        )

        presentations = await self.crear_texto(
            guild, "🙋・presentaciones", community
        )

        suggestions = await self.crear_texto(
            guild, "💡・sugerencias", community
        )

        memes = await self.crear_texto(
            guild, "😂・memes", community
        )

        # VOZ
        await self.crear_voz(guild, "🔊 General", voice)
        await self.crear_voz(guild, "🎮 Gaming", voice)
        await self.crear_voz(guild, "🎵 Música", voice)

        # STAFF
        await self.crear_texto(
            guild, "💬・staff-chat", staff_category
        )

        await self.crear_texto(
            guild, "📋・logs", staff_category
        )

        # PANEL DE REGLAS
        rules_embed = discord.Embed(
            title="📜 REGLAS DEL SERVIDOR",
            description=(
                "**1.** Respetar a todos los miembros.\n\n"
                "**2.** No insultar ni acosar.\n\n"
                "**3.** No hacer spam ni publicidad sin permiso.\n\n"
                "**4.** No enviar contenido inapropiado.\n\n"
                "**5.** Respetar las indicaciones del staff.\n\n"
                "**6.** No utilizar canales incorrectamente.\n\n"
                "**7.** Disfrutar y mantener una buena comunidad."
            ),
            color=discord.Color.blurple()
        )

        rules_embed.set_footer(
            text="Al permanecer en el servidor aceptás estas reglas."
        )

        await rules.send(embed=rules_embed)

        # PANEL DE REACTION ROLES
        role_embed = discord.Embed(
            title="🎭 SELECCIONÁ TUS ROLES",
            description=(
                "Reaccioná al mensaje para recibir tus roles.\n\n"
                "🎮 — Gamer\n"
                "🎨 — Creativo\n"
                "🎵 — Música"
            ),
            color=discord.Color.green()
        )

        role_message = await roles_channel.send(
            embed=role_embed
        )

        reactions = {
            "🎮": gamer.id,
            "🎨": creative.id,
            "🎵": music.id
        }

        for emoji in reactions:
            await role_message.add_reaction(emoji)

        self.config[str(guild.id)] = {
            "role_message": role_message.id,
            "reactions": reactions
        }

        save_config(self.config)

        # PANEL DE TICKETS
        ticket_embed = discord.Embed(
            title="🎫 CENTRO DE SOPORTE",
            description=(
                "¿Necesitás ayuda?\n\n"
                "Presioná el botón para abrir un ticket privado "
                "con nuestro equipo de soporte."
            ),
            color=discord.Color.blurple()
        )

        await self.crear_texto(
            guild, "🎫・abrir-ticket", support
        )

        ticket_channel = discord.utils.get(
            support.text_channels,
            name="🎫・abrir-ticket"
        )

        await ticket_channel.send(
            embed=ticket_embed,
            view=TicketPanel(self)
        )

        # BIENVENIDA
        welcome_embed = discord.Embed(
            title="👋 ¡BIENVENIDO!",
            description=(
                "¡Gracias por unirte a nuestra comunidad!\n"
                "Leé las reglas y elegí tus roles."
            ),
            color=discord.Color.green()
        )

        await welcome.send(embed=welcome_embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = discord.utils.get(
            member.guild.roles,
            name="Comunidad"
        )

        if role:
            await member.add_roles(role)

        channel = discord.utils.get(
            member.guild.text_channels,
            name="👋・bienvenida"
        )

        if channel:
            await channel.send(
                f"👋 ¡Bienvenido/a {member.mention}!"
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member and payload.member.bot:
            return

        await self.procesar_reaccion(payload, True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.procesar_reaccion(payload, False)

    async def procesar_reaccion(self, payload, agregar):
        data = self.config.get(str(payload.guild_id))

        if not data:
            return

        if payload.message_id != data.get("role_message"):
            return

        role_id = data.get("reactions", {}).get(
            str(payload.emoji)
        )

        if not role_id:
            return

        guild = self.bot.get_guild(payload.guild_id)

        if guild is None:
            return

        member = guild.get_member(payload.user_id)

        if member is None or member.bot:
            return

        role = guild.get_role(role_id)

        if role is None:
            return

        try:
            if agregar:
                await member.add_roles(role)
            else:
                await member.remove_roles(role)
        except discord.Forbidden:
            pass

    @app_commands.command(
        name="crear_servidor",
        description="Organiza automáticamente todo el servidor."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def crear_servidor(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🚀 **¿Querés que organice automáticamente tu servidor?**\n\n"
            "Voy a crear categorías, canales, roles, reglas, "
            "reaction roles y tickets.\n\n"
            "No voy a borrar tus canales existentes.",
            view=ConfirmarServidor(self),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ServidorAutomatico(bot))
