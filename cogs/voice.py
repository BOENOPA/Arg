import asyncio
import discord
from discord import app_commands
from discord.ext import commands
# ============================================================
# COLORES
# ============================================================
PURPLE = discord.Color.from_rgb(115, 55, 210)
GREEN = discord.Color.from_rgb(45, 190, 110)
RED = discord.Color.from_rgb(220, 60, 70)
# ============================================================
# COG
# ============================================================
class Voice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Canal donde el bot debe permanecer conectado
        self.voice_channels = {}
        # Evita múltiples tareas de reconexión al mismo tiempo
        self.reconnect_tasks = {}
        print("[VOICE] Cog de voz cargado correctamente.")
    # ========================================================
    # /vc
    # ========================================================
    @app_commands.command(
        name="vc",
        description="Hace que el bot se una a tu canal de voz."
    )
    async def vc(self, interaction: discord.Interaction):
        print(
            f"[VOICE] /vc ejecutado por "
            f"{interaction.user} ({interaction.user.id})"
        )
        # ----------------------------------------------------
        # COMPROBAR SERVIDOR
        # ----------------------------------------------------
        if interaction.guild is None:
            print("[VOICE] ❌ Comando utilizado fuera de un servidor.")
            await interaction.response.send_message(
                "❌ Este comando solamente funciona dentro de un servidor.",
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # COMPROBAR CANAL DEL USUARIO
        # ----------------------------------------------------
        miembro = interaction.guild.get_member(interaction.user.id)
        if miembro is None:
            print("[VOICE] ❌ No se pudo encontrar al miembro.")
            await interaction.response.send_message(
                "❌ No pude encontrar tu usuario en el servidor.",
                ephemeral=True
            )
            return
        if miembro.voice is None or miembro.voice.channel is None:
            print(
                f"[VOICE] ❌ {interaction.user} no está en un canal de voz."
            )
            await interaction.response.send_message(
                "❌ Tenés que estar conectado a un canal de voz.",
                ephemeral=True
            )
            return
        canal = miembro.voice.channel
        print(
            f"[VOICE] Canal solicitado: "
            f"#{canal.name} ({canal.id})"
        )
        # ----------------------------------------------------
        # COMPROBAR PERMISOS
        # ----------------------------------------------------
        permisos = canal.permissions_for(interaction.guild.me)
        if not permisos.connect:
            print("[VOICE] ❌ El bot no tiene permiso CONNECT.")
            await interaction.response.send_message(
                "❌ No tengo permiso para conectarme a ese canal.",
                ephemeral=True
            )
            return
        if not permisos.speak:
            print(
                "[VOICE] ⚠️ El bot no tiene permiso SPEAK. "
                "Se intentará conectar igualmente."
            )
        # ----------------------------------------------------
        # RESPONDER ANTES DE CONECTAR
        # ----------------------------------------------------
        await interaction.response.defer(ephemeral=True)
        # ----------------------------------------------------
        # VOICE CLIENT ACTUAL
        # ----------------------------------------------------
        voice_client = interaction.guild.voice_client
        # ----------------------------------------------------
        # YA ESTÁ EN ESE CANAL
        # ----------------------------------------------------
        if voice_client is not None and voice_client.is_connected():
            if voice_client.channel.id == canal.id:
                print(
                    f"[VOICE] ✅ El bot ya está en #{canal.name}."
                )
                # Aseguramos mute y deaf
                try:
                    await voice_client.guild.change_voice_state(
                        channel=canal,
                        self_mute=True,
                        self_deaf=True
                    )
                    print(
                        "[VOICE] 🔇 Bot configurado como "
                        "muteado y sordo."
                    )
                except Exception as error:
                    print(
                        f"[VOICE] ⚠️ No se pudo actualizar "
                        f"mute/deaf: {error}"
                    )
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="🔊 Ya estoy conectado",
                        description=(
                            f"Ya estoy en {canal.mention}.\n\n"
                            "🔇 **Micrófono:** muteado\n"
                            "🙉 **Audio:** desactivado"
                        ),
                        color=PURPLE
                    ),
                    ephemeral=True
                )
                return
            # ------------------------------------------------
            # MOVER AL NUEVO CANAL
            # ------------------------------------------------
            print(
                f"[VOICE] 🔄 Moviendo bot de "
                f"#{voice_client.channel.name} a #{canal.name}."
            )
            try:
                await voice_client.move_to(canal)
                # Asegurar mute/deaf
                try:
                    await voice_client.guild.change_voice_state(
                        channel=canal,
                        self_mute=True,
                        self_deaf=True
                    )
                except Exception as error:
                    print(
                        f"[VOICE] ⚠️ Error configurando mute/deaf: "
                        f"{error}"
                    )
                self.voice_channels[interaction.guild.id] = canal.id
                print(
                    f"[VOICE] ✅ Bot movido correctamente a #{canal.name}."
                )
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="🔊 Canal cambiado",
                        description=(
                            f"Me moví a {canal.mention}.\n\n"
                            "🔇 **Micrófono:** muteado\n"
                            "🙉 **Audio:** desactivado"
                        ),
                        color=GREEN
                    ),
                    ephemeral=True
                )
                return
            except Exception as error:
                print(
                    f"[VOICE] ❌ Error moviendo el bot: {error}"
                )
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Error",
                        description=(
                            "No pude moverme al canal de voz.\n\n"
                            f"`{error}`"
                        ),
                        color=RED
                    ),
                    ephemeral=True
                )
                return
        # ----------------------------------------------------
        # CONECTAR DESDE CERO
        # ----------------------------------------------------
        print(
            f"[VOICE] 🔊 Conectando a #{canal.name}..."
        )
        try:
            # Si existe una conexión vieja, cerrarla
            if voice_client is not None:
                print(
                    "[VOICE] ⚠️ Existe una conexión anterior. "
                    "Cerrándola..."
                )
                try:
                    await voice_client.disconnect(force=True)
                except Exception as error:
                    print(
                        f"[VOICE] ⚠️ Error cerrando conexión anterior: "
                        f"{error}"
                    )
            # ------------------------------------------------
            # CONEXIÓN
            # ------------------------------------------------
            voice_client = await canal.connect(
                timeout=30,
                reconnect=True,
                self_deaf=True,
                self_mute=True
            )
            self.voice_channels[interaction.guild.id] = canal.id
            print(
                f"[VOICE] ✅ Conectado correctamente a #{canal.name}."
            )
            print(
                "[VOICE] 🔇 Micrófono: MUTEADO"
            )
            print(
                "[VOICE] 🙉 Audio recibido: DESACTIVADO"
            )
            # ------------------------------------------------
            # ASEGURAR ESTADO MUTE/DEAF
            # ------------------------------------------------
            try:
                await voice_client.guild.change_voice_state(
                    channel=canal,
                    self_mute=True,
                    self_deaf=True
                )
                print(
                    "[VOICE] ✅ Estado mute/deaf confirmado."
                )
            except Exception as error:
                print(
                    f"[VOICE] ⚠️ No se pudo confirmar "
                    f"mute/deaf: {error}"
                )
            await interaction.followup.send(
                embed=discord.Embed(
                    title="🔊 Conectado",
                    description=(
                        f"Me uní a {canal.mention}.\n\n"
                        "🔇 **Micrófono:** muteado\n"
                        "🙉 **Audio:** desactivado\n"
                        "🔄 **Reconexión automática:** activada"
                    ),
                    color=GREEN
                ),
                ephemeral=True
            )
        except asyncio.TimeoutError:
            print(
                "[VOICE] ❌ Tiempo agotado conectando al canal."
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Tiempo agotado",
                    description=(
                        "Discord tardó demasiado en establecer "
                        "la conexión de voz."
                    ),
                    color=RED
                ),
                ephemeral=True
            )
        except Exception as error:
            print(
                f"[VOICE] ❌ Error conectando al canal: {error}"
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ No pude conectarme",
                    description=(
                        "Ocurrió un error al conectarme al canal "
                        "de voz.\n\n"
                        f"```{error}```"
                    ),
                    color=RED
                ),
                ephemeral=True
            )
    # ========================================================
    # /vcsalir
    # ========================================================
    @app_commands.command(
        name="vcsalir",
        description="Hace que el bot salga del canal de voz."
    )
    async def vcsalir(self, interaction: discord.Interaction):
        print(
            f"[VOICE] /vcsalir ejecutado por "
            f"{interaction.user} ({interaction.user.id})"
        )
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solamente funciona dentro de un servidor.",
                ephemeral=True
            )
            return
        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_connected():
            print(
                "[VOICE] ⚠️ El bot no está conectado a voz."
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="🔊 No estoy conectado",
                    description="No estoy conectado a ningún canal de voz.",
                    color=RED
                ),
                ephemeral=True
            )
            return
        canal_anterior = voice_client.channel
        print(
            f"[VOICE] 🚪 Saliendo de #{canal_anterior.name}..."
        )
        # Cancelar tarea de reconexión
        task = self.reconnect_tasks.pop(interaction.guild.id, None)
        if task is not None and not task.done():
            task.cancel()
            print(
                "[VOICE] 🛑 Tarea de reconexión cancelada."
            )
        try:
            await voice_client.disconnect(force=True)
            self.voice_channels.pop(interaction.guild.id, None)
            print(
                f"[VOICE] ✅ Bot salió de #{canal_anterior.name}."
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="👋 Salí del canal",
                    description=(
                        f"Salí de {canal_anterior.mention}."
                    ),
                    color=PURPLE
                ),
                ephemeral=True
            )
        except Exception as error:
            print(
                f"[VOICE] ❌ Error saliendo del canal: {error}"
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description=(
                        f"No pude salir del canal.\n\n"
                        f"```{error}```"
                    ),
                    color=RED
                ),
                ephemeral=True
            )
    # ========================================================
    # RECONEXIÓN AUTOMÁTICA
    # ========================================================
    async def reconnect_voice(
        self,
        guild: discord.Guild,
        channel_id: int
    ):
        guild_id = guild.id
        # Evitar duplicar tareas
        existing_task = self.reconnect_tasks.get(guild_id)
        if (
            existing_task is not None
            and not existing_task.done()
        ):
            return
        async def reconnect_loop():
            intento = 0
            while True:
                intento += 1
                try:
                    canal = guild.get_channel(channel_id)
                    if canal is None:
                        print(
                            f"[VOICE] ❌ No encuentro el canal "
                            f"{channel_id}."
                        )
                        return
                    print(
                        f"[VOICE] 🔄 Reconexión automática "
                        f"#{intento} a #{canal.name}..."
                    )
                    voice_client = guild.voice_client
                    # Si ya está conectado, no hacer nada
                    if (
                        voice_client is not None
                        and voice_client.is_connected()
                    ):
                        print(
                            "[VOICE] ✅ La conexión ya está activa."
                        )
                        return
                    # Limpiar conexión vieja
                    if voice_client is not None:
                        try:
                            await voice_client.disconnect(
                                force=True
                            )
                        except Exception:
                            pass
                    # Intentar conectar
                    voice_client = await canal.connect(
                        timeout=30,
                        reconnect=True,
                        self_deaf=True,
                        self_mute=True
                    )
                    self.voice_channels[guild_id] = channel_id
                    print(
                        f"[VOICE] ✅ Reconectado correctamente "
                        f"a #{canal.name}."
                    )
                    print(
                        "[VOICE] 🔇 Micrófono: MUTEADO"
                    )
                    print(
                        "[VOICE] 🙉 Audio: DESACTIVADO"
                    )
                    # Confirmar mute/deaf
                    try:
                        await voice_client.guild.change_voice_state(
                            channel=canal,
                            self_mute=True,
                            self_deaf=True
                        )
                    except Exception as error:
                        print(
                            f"[VOICE] ⚠️ No se pudo confirmar "
                            f"mute/deaf: {error}"
                        )
                    return
                except asyncio.CancelledError:
                    print(
                        "[VOICE] 🛑 Reconexión cancelada."
                    )
                    return
                except Exception as error:
                    print(
                        f"[VOICE] ❌ Falló reconexión #{intento}: "
                        f"{error}"
                    )
                    # Esperar antes del siguiente intento
                    espera = min(60, 5 * intento)
                    print(
                        f"[VOICE] ⏳ Reintentando en "
                        f"{espera} segundos..."
                    )
                    await asyncio.sleep(espera)
        self.reconnect_tasks[guild_id] = asyncio.create_task(
            reconnect_loop()
        )
    # ========================================================
    # EVENTO: CAMBIO DE ESTADO DE VOZ
    # ========================================================
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        # Solo nos interesa el propio bot
        if member.id != self.bot.user.id:
            return
        guild = member.guild
        # ----------------------------------------------------
        # BOT DESCONECTADO
        # ----------------------------------------------------
        if before.channel is not None and after.channel is None:
            channel_id = self.voice_channels.get(guild.id)
            if channel_id is None:
                return
            print(
                f"[VOICE] ⚠️ El bot fue desconectado de "
                f"#{before.channel.name}."
            )
            print(
                "[VOICE] 🔄 Iniciando reconexión automática..."
            )
            await self.reconnect_voice(
                guild,
                channel_id
            )
            return
        # ----------------------------------------------------
        # BOT MOVIDO
        # ----------------------------------------------------
        if (
            before.channel is not None
            and after.channel is not None
            and before.channel.id != after.channel.id
        ):
            print(
                f"[VOICE] 🔄 El bot cambió de canal: "
                f"#{before.channel.name} → #{after.channel.name}"
            )
            self.voice_channels[guild.id] = after.channel.id
        # ----------------------------------------------------
        # ASEGURAR MUTE
        # ----------------------------------------------------
        if after.channel is not None:
            if not after.self_mute:
                print(
                    "[VOICE] ⚠️ El bot dejó de estar muteado. "
                    "Volviendo a mutear..."
                )
                try:
                    await guild.change_voice_state(
                        channel=after.channel,
                        self_mute=True,
                        self_deaf=True
                    )
                    print(
                        "[VOICE] 🔇 Bot muteado nuevamente."
                    )
                except Exception as error:
                    print(
                        f"[VOICE] ❌ Error aplicando mute: {error}"
                    )
    # ========================================================
    # SETUP
    # ========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(Voice(bot))
    print(
        "[VOICE] ✅ cogs.voice cargado correctamente."
    )