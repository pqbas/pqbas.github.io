---
title: Notes
---

<div class="home notes-page">

<div class="home-name">
  <a class="back" href="/">← Percy Cubas</a>
</div>

<h1 class="notes-title">Notes</h1>
<p>Things I learn while building, written as short guides. In Spanish.</p>

<input class="notes-search" type="search" placeholder="Search notes…" aria-label="Search notes" oninput="const n=t=>t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');const q=n(this.value);const p=document.querySelector('.notes-page');p.querySelectorAll('.home-row').forEach(r=>{r.hidden=!n(r.textContent).includes(q)});p.querySelectorAll('.notes-group, .home-section').forEach(g=>{g.hidden=!g.querySelector('.home-row:not([hidden])')})">

<section class="home-section" id="ai-agents">
  <h2>AI agents</h2>
  <div class="notes-group">
    <h3>Support agent tutorial</h3>
    <a class="home-row simple" href="/notes/tutoriales/agente-soporte/1-agente-minimo"><span class="title">1. Crear un agente mínimo con LangGraph</span></a>
    <a class="home-row simple" href="/notes/tutoriales/agente-soporte/2-herramientas"><span class="title">2. Darle herramientas al agente</span></a>
    <a class="home-row simple" href="/notes/tutoriales/agente-soporte/3-humano-en-el-bucle"><span class="title">3. Pedir aprobación a un humano</span></a>
    <a class="home-row simple" href="/notes/tutoriales/agente-soporte/4-rag"><span class="title">4. Responder con los documentos de la tienda (RAG)</span></a>
    <a class="home-row simple" href="/notes/tutoriales/agente-soporte/5-mcp"><span class="title">5. Usar herramientas desde un servidor MCP</span></a>
  </div>
  <div class="notes-group">
    <h3>Security</h3>
    <a class="home-row simple" href="/notes/ai/guardrails"><span class="title">Guardrails en aplicaciones con LLM</span></a>
    <a class="home-row simple" href="/notes/ai/secure-by-design"><span class="title">Secure by Design en aplicaciones con LLM</span></a>
    <a class="home-row simple" href="/notes/ai/infra-privada"><span class="title">Infraestructura privada para un agente LLM en AWS</span></a>
  </div>
</section>

<!-- Hidden until these notes are polished (see ignorePatterns in quartz.config.yaml).

<section class="home-section" id="system-design">
  <h2>System design</h2>
  <div class="notes-group">
    <h3>Designs</h3>
    <a class="home-row simple" href="/notes/system-design/chat-con-ia"><span class="title">Chat con IA</span></a>
    <a class="home-row simple" href="/notes/system-design/acortador-de-urls"><span class="title">Acortador de URLs</span></a>
    <a class="home-row simple" href="/notes/system-design/acortador-de-urls-avanzado"><span class="title">Acortador de URLs avanzado</span></a>
    <a class="home-row simple" href="/notes/system-design/blog"><span class="title">Plataforma de blogs</span></a>
    <a class="home-row simple" href="/notes/system-design/todo-app"><span class="title">Todo app</span></a>
  </div>
  <div class="notes-group">
    <h3>Basics</h3>
    <a class="home-row simple" href="/notes/system-design/constantes-para-estimar"><span class="title">Constantes para estimar sistemas</span></a>
    <a class="home-row simple" href="/notes/system-design/criterios-para-elegir-servicios"><span class="title">Criterios para elegir servicios</span></a>
  </div>
</section>

<section class="home-section" id="full-stack">
  <h2>Full stack</h2>
  <div class="notes-group">
    <h3>Todo app tutorial</h3>
    <a class="home-row simple" href="/notes/tutoriales/todo-app/1-crear-una-api"><span class="title">1. Crear una API desde cero</span></a>
    <a class="home-row simple" href="/notes/tutoriales/todo-app/2-conectar-una-base-de-datos"><span class="title">2. Conectar una API a una base de datos</span></a>
    <a class="home-row simple" href="/notes/tutoriales/todo-app/3-crear-un-frontend"><span class="title">3. Crear un frontend desde cero</span></a>
    <a class="home-row simple" href="/notes/tutoriales/todo-app/4-conectar-un-frontend-a-una-api"><span class="title">4. Conectar un frontend a una API</span></a>
  </div>
</section>

<section class="home-section" id="cloud-and-data">
  <h2>Cloud and data</h2>
  <div class="notes-group">
    <h3>AWS</h3>
    <a class="home-row simple" href="/notes/aws/pipeline-de-documentos-con-step-functions"><span class="title">Pipeline de procesamiento de documentos con Step Functions y Lambda</span></a>
    <a class="home-row simple" href="/notes/aws/cors-s3-para-desarrollo-local"><span class="title">Permitir localhost en el CORS de un bucket S3 con URLs prefirmadas</span></a>
  </div>
  <div class="notes-group">
    <h3>Databases</h3>
    <a class="home-row simple" href="/notes/databases/indices"><span class="title">Índices en bases de datos</span></a>
    <a class="home-row simple" href="/notes/snowflake/fundamentos"><span class="title">Fundamentos de Snowflake</span></a>
    <a class="home-row simple" href="/notes/alembic/migraciones"><span class="title">Aplicar migraciones de base de datos con Alembic</span></a>
  </div>
</section>

<section class="home-section" id="linux">
  <h2>Linux</h2>
  <div class="notes-group">
    <a class="home-row simple" href="/notes/network/conectarse-a-una-red-wifi"><span class="title">Conectarse a una red WiFi desde la terminal en Linux</span></a>
    <a class="home-row simple" href="/notes/network/descubrimiento-de-dispositivos"><span class="title">Descubrimiento de dispositivos por IP en una red local</span></a>
    <a class="home-row simple" href="/notes/linux/cambiar-la-hora"><span class="title">Cambiar la hora y la zona horaria en Linux</span></a>
    <a class="home-row simple" href="/notes/hyprland/recuperar-sesion-bloqueada"><span class="title">Recuperar una sesión de Hyprland con el bloqueo colgado</span></a>
  </div>
</section>

<section class="home-section">
  <h2>Interviews</h2>
  <div class="notes-group">
    <a class="home-row simple" href="/notes/entrevistas/temas-a-revisar"><span class="title">Temas a revisar para entrevistas técnicas</span></a>
  </div>
</section>

-->

</div>
