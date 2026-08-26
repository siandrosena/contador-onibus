# 🚌 Contador de Passageiros em Ônibus — Visão Computacional (YOLOv8 + ByteTrack)

> Sistema de contagem automática de passageiros por vídeo, usando detecção de objetos (YOLOv8) e rastreamento (ByteTrack), com deduplicação por troca de ID e exportação de logs em CSV.

*(English summary below ⬇️)*

---

## 🎯 O problema

Na operação de transporte de passageiros, saber **quantas pessoas realmente embarcaram** é essencial para planejar rota, escala e receita. Contagem manual é cara, falha e não escala. A pergunta era: **dá para contar passageiros automaticamente a partir do vídeo da câmera do ônibus?**

## 💡 A solução

Um pipeline de visão computacional que:

- **Detecta pessoas** em tempo real com **YOLOv8**
- **Rastreia cada pessoa** entre frames com **ByteTrack** (mantém um ID por indivíduo)
- Define uma **ROI na porta** e uma **linha de contagem** — só conta quem cruza a linha na direção certa
- **Deduplica eventos** por troca de ID (evita contar a mesma pessoa duas vezes quando o tracker perde e reatribui o ID)
- **Exporta logs em CSV** com corte de horário configurável (ex.: 20:30–24:30)

## ⚙️ Como funciona

```
Vídeo → YOLOv8 (detecção) → ByteTrack (rastreamento por ID)
      → ROI da porta + linha de contagem
      → regra de cruzamento + deduplicação de ID
      → log CSV (timestamp, evento, contagem)
```

## 🧰 Stack

- **Python**
- **YOLOv8** (Ultralytics) — detecção de objetos
- **ByteTrack** — rastreamento multi-objeto
- **OpenCV** — processamento de vídeo
- Saída em **CSV** para análise

## 📊 Impacto

- Elimina a contagem manual de passageiros
- Gera dado confiável para **decisão de rota, escala e receita**
- Base para indicadores operacionais (fluxo por horário, pico de embarque)

## 🌍 Contexto real

Projeto nascido de uma necessidade real de uma **empresa de transporte de passageiros**, onde atuo estruturando dados operacionais e construindo automações com IA para reduzir desperdício e apoiar decisão.

---

## 🇬🇧 English summary

**Bus passenger counter using computer vision (YOLOv8 + ByteTrack).**
Real-time person detection (YOLOv8) + multi-object tracking (ByteTrack), with a door ROI and a counting line. Counts only people crossing the line in the right direction, deduplicates events on tracker ID switches, and exports CSV logs with a configurable time cut (e.g. 20:30–24:30). Built to replace manual passenger counting in a passenger-transport operation and to feed operational KPIs (boarding flow by time, peak hours).

**Stack:** Python · YOLOv8 (Ultralytics) · ByteTrack · OpenCV · CSV output.

---

## 👤 Autor

**Siandro Sena** — Engenheiro (Produção / Materiais), MBA em Inteligência Artificial. Automação de processos com IA, dados e eficiência operacional.
🔗 [LinkedIn](https://www.linkedin.com/in/siandro-sena-847712314)
