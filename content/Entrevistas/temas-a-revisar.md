---
title: Temas a revisar para entrevistas técnicas
tags:
  - entrevistas
  - patrones
  - seguridad
  - react
  - arquitectura
  - aws
---

Ordenados por prioridad. Arriba lo que preguntaron en la entrevista y no
pude responder bien.

## 1. Patrones de diseño, con preguntas de caso

- [ ] Los 23 patrones GoF: qué problema resuelve cada uno
- [ ] Pares que se confunden: Strategy vs State, Adapter vs Facade vs Decorator vs Proxy, Factory Method vs Abstract Factory vs Builder, Observer vs Mediator
- [ ] Práctica: leer un escenario, elegir el patrón y explicar por qué no es el otro

## 2. Principios de diseño

- [ ] SOLID, con un ejemplo de cada uno
- [ ] DRY, KISS, YAGNI, composición sobre herencia
- [ ] Inyección de dependencias

## 3. Autenticación y autorización

- [ ] Diferencia entre autenticación y autorización, 401 vs 403
- [ ] Sesiones con cookie, JWT, OAuth 2.0, OpenID Connect, API keys, mTLS, MFA, SAML
- [ ] JWT por dentro: header, payload, firma, expiración, refresh token
- [ ] Dónde guardar el token en el front: cookie httpOnly vs localStorage

## 4. Seguridad de APIs

- [ ] OWASP Top 10: inyección, XSS, CSRF, control de acceso roto
- [ ] CORS, rate limiting, validación de entrada, manejo de secretos, HTTPS

## 5. React y frontend

- [ ] Hooks: useState, useEffect, useMemo, useCallback, useRef, useContext, hooks personalizados
- [ ] Ciclo de render y cuándo se vuelve a ejecutar un efecto
- [ ] Manejo de estado: local, Context, Zustand, Redux Toolkit; estado de servidor con TanStack Query

## 6. Arquitectura de software

- [ ] Monolito vs microservicios; capas, hexagonal, clean architecture
- [ ] Patrones de integración: Repository, Circuit Breaker, Retry, Saga, CQRS, Pub/Sub, idempotencia
- [ ] Caché, colas, escalado horizontal, teorema CAP

## 7. Cloud y AWS

- [ ] Lambda vs Fargate vs EC2: cuándo usar cada uno
- [ ] API Gateway, Cognito, DynamoDB vs RDS, S3, Secrets Manager, IAM y mínimo privilegio

## 8. Cómo responder en una entrevista

- [ ] Responder en voz alta y con estructura: qué es, cuándo se usa, un ejemplo
- [ ] Defender las decisiones del propio proyecto: por qué Lambda, por qué BM25, qué cambiaría en producción

## 9. Entorno para entrevistas

- [ ] Teams en Chrome o Edge, compartiendo una ventana, probado antes de cada entrevista
