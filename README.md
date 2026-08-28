# 🚌 Quantas pessoas embarcaram de verdade no seu ônibus?

> Sistema que conta passageiros automaticamente pelo vídeo da câmera do ônibus — sem planilha manual, sem alguém contando cabeça na porta.

*(English summary below ⬇️)*

---

## 🎯 O problema

Numa operação de transporte de passageiros, saber quantas pessoas realmente embarcaram é essencial pra planejar rota, escala e receita. Contagem manual é cara, falha, e não escala pra uma frota inteira. Câmera sozinha também não resolve — vídeo cru não vira número, e um contador ingênuo conta a mesma pessoa duas vezes toda hora que perde o rastro dela por um instante (alguém passa na frente, a luz muda, o ângulo trava).

## 💡 A solução

O sistema assiste o vídeo, detecta cada pessoa, segue ela frame a frame por um ID, e só conta quando ela cruza a linha da porta na direção certa — uma vez, não importa quantas vezes o rastreador "pisque".

### O problema que mais gera contagem errada — resolvido

O rastreador de vídeo, na prática, perde o rastro de uma pessoa por 1-2 frames e a reencontra com um **ID novo** (a mesma pessoa física vira "pessoa nova" pro sistema). Um contador ingênuo conta ela de novo. O deste projeto reconhece a troca de ID pela posição — se um ID some e um ID novo aparece bem perto, no mesmo lugar, um instante depois, é a mesma pessoa continuando, não uma pessoa nova:

```
Pessoa (ID 1) cruza a linha da porta → contada (total: 1)
Rastreador perde o ID 1 por 1 frame (oclusão momentânea)
Reaparece como ID 2, a 2px de distância, 1 frame depois
→ sistema reconhece: é a mesma pessoa → NÃO conta de novo (total continua: 1)
```

Esse comportamento está coberto por teste automatizado, não é só uma promessa no README.

## 🔑 Por que isso importa

- **Substitui a contagem manual** de passageiros, sem custo recorrente de mão de obra.
- **Dado confiável pra decisão real**: rota, escala, receita, indicador de pico de embarque por horário.
- **Não infla número por erro de rastreamento** — o problema mais comum de "contador de gente por câmera" (contar em dobro) é tratado de propósito, não ignorado.

---

## 🧰 Por baixo do capô (pra quem quiser entrar no código)

```
Vídeo → YOLOv8 (detecção) → ByteTrack (rastreamento por ID)
      → ROI da porta + linha de contagem
      → regra de cruzamento + deduplicação de troca de ID
      → log CSV (timestamp, evento, contagem)
```

### Como rodar

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

python src/counter.py --source caminho/do/video.mp4 --save-video
```

Principais opções:

| Flag | Descrição |
|---|---|
| `--line` | Linha de contagem `x1,y1,x2,y2`. Valores ≤1 são tratados como razão do frame (padrão: linha horizontal no meio) |
| `--conf` | Confiança mínima de detecção (padrão 0.35) |
| `--video-start-time` | Horário real (HH:MM) do início do vídeo, para calcular timestamp dos eventos |
| `--window-start` / `--window-end` | Só loga eventos dentro do corte de horário (ex.: `20:30` / `24:30`) |
| `--save-video` | Salva vídeo anotado com caixas, IDs e linha de contagem |

### Testes

```bash
pip install -r requirements-dev.txt
pytest tests/
```

Os testes cobrem a lógica de negócio que não depende do modelo (`src/crossing.py`): detecção de cruzamento de linha, direção (entrada/saída) e a deduplicação por troca de ID do tracker — o núcleo do que o pipeline promete resolver.

`scripts/make_demo_video.py` gera um vídeo sintético (formas geométricas, não pessoas) só para smoke test do pipeline ponta a ponta — leitura de vídeo, chamada ao YOLO+ByteTrack e escrita do CSV. Não valida acurácia de detecção; para isso, aponte `--source` para um vídeo real com pessoas.

### Stack

- **Python**
- **YOLOv8** (Ultralytics) — detecção de objetos
- **ByteTrack** — rastreamento multi-objeto
- **OpenCV** — processamento de vídeo
- Saída em **CSV** para análise

### ⚠️ Limitações conhecidas

- **Testado com câmeras reais de veículos diferentes: funcionou bem numa, confundiu em outra.** Ângulo, posição e qualidade de câmera diferentes entre veículos afetam a detecção/rastreamento — o sistema não generaliza automaticamente pra qualquer câmera sem calibrar `--line`, `--conf` e, possivelmente, a posição de instalação da câmera por veículo.
- O smoke test automatizado usa um vídeo sintético (formas geométricas) só pra provar que o pipeline roda ponta a ponta — a validação de acurácia real depende de testar com câmera/vídeo de cada veículo.
- **A dedução de troca de ID é geométrica (distância + janela de frames), não visual** — não compara a aparência da pessoa, só posição. Duas pessoas diferentes cruzando muito perto uma da outra, no mesmo instante, podem confundir o sistema.
- **Uma única linha de contagem** — não lida com múltiplas portas/entradas no mesmo vídeo sem rodar o script mais de uma vez com linhas diferentes.

## 🌍 Contexto real

Projeto nascido de uma necessidade real de uma **empresa de transporte de passageiros**, onde atuo estruturando dados operacionais e construindo automações com IA para reduzir desperdício e apoiar decisão.

---

## 🇬🇧 English summary

**How many passengers actually boarded your bus?** A system that counts passengers automatically from the bus camera's video — no manual headcount, no spreadsheet. Real-time person detection (YOLOv8) + multi-object tracking (ByteTrack), with a door ROI and counting line. The hardest real-world failure mode — the tracker losing and re-assigning an ID mid-crossing, which naively double-counts the same person — is detected and deduplicated by design, covered by automated tests. Exports CSV logs with a configurable time cut (e.g. 20:30–24:30). Built to replace manual passenger counting in a passenger-transport operation and to feed operational KPIs.

**Stack:** Python · YOLOv8 (Ultralytics) · ByteTrack · OpenCV · CSV output.

---

## 👤 Autor

**Siandro Sena** — Engenheiro (Produção / Materiais), MBA em Inteligência Artificial. Automação de processos com IA, dados e eficiência operacional.
🔗 [LinkedIn](https://www.linkedin.com/in/siandro-sena-847712314)
