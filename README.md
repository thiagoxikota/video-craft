# Video Craft

**Uma skill para transformar filmagem em vídeo editado, com direção, som e verificação do arquivo final.**

[English](docs/README.en.md) · [Instalação](#instalação) · [Exemplo executável](#teste-em-dois-minutos) · [Como funciona](skills/video-craft/SKILL.md)

Video Craft reúne o processo de edição usado por Thiago Xikota em uma skill portátil para Claude Code e outros agentes com acesso a arquivos e terminal. O pacote inclui instruções editoriais, referências de som e licenciamento, um instalador e uma CLI que renderiza mídia de verdade com FFmpeg.

O agente inspeciona os planos, organiza a narrativa, escolhe uma composição adequada e verifica o export. O julgamento visual e sonoro continua fazendo parte do trabalho.

## O que vem no pacote

| Parte | Entrega |
|---|---|
| Direção editorial | Brief, seleção de planos, ritmo, hierarquia e gráficos com propósito |
| Som | Gênero, som direto, música, efeitos, versões sem trilha e proveniência |
| CLI local | Inspeção, contact sheet, montagem por timeline JSON, masterização e QA |
| Motion | Orientação para usar Remotion quando a composição pede camadas e animação |
| Distribuição | Skill independente, plugin Claude Code e ZIP para ambientes compatíveis |

Não inclui gerador de vídeo por IA, download de músicas, vozes, assets de clientes ou renderizador Remotion. A CLI faz cortes diretos; camadas, títulos animados e transições exigem uma composição separada.

## Instalação

### Claude Code: plugin

Dentro do Claude Code:

```text
/plugin marketplace add thiagoxikota/video-craft
/plugin install video-craft@video-craft-tools
```

Depois, peça algo como:

```text
/video-craft:video-craft Monte um recap vertical de 30 segundos com os vídeos em ./media.
Quero foco nas pessoas e no resultado, gráficos que ajudem a contar a história,
uma versão de revisão com trilha e uma versão sem música.
```

Este é um marketplace independente, sem afiliação com a Anthropic. O plugin contém a skill e seus arquivos; não instala hooks, servidores ou dependências.

### Skill local: Claude ou Codex

```bash
git clone https://github.com/thiagoxikota/video-craft.git
cd video-craft
python3 install.py --target claude --project /caminho/do/projeto
```

Para Codex, troque `--target claude` por `--target codex`. Para todos os projetos da sua conta, use `--scope user`. Confira antes com `--dry-run`. O instalador recusa substituir uma skill existente; nenhuma configuração global é editada e nenhum pacote é baixado.

### Claude com upload de skill

O [release](https://github.com/thiagoxikota/video-craft/releases/latest) inclui `video-craft-skill.zip`. Em uma conta com Skills habilitadas, adicione-o em **Customize → Skills**. A disponibilidade de execução e de FFmpeg depende desse ambiente. Upload da skill não instala binários nem garante renderização; o agente deve informar quando só conseguiu preparar o projeto. O fluxo executável deste repositório foi testado localmente, não em todos os planos do Claude.

## Dependências de renderização

- Python 3.10 ou superior.
- FFmpeg e ffprobe, com os encoders `libx264` e `aac`.
- Espaço em disco para os arquivos intermediários.

Se precisar instalar FFmpeg:

```bash
# macOS com Homebrew
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg python3
```

No Windows, consulte as [distribuições indicadas pelo FFmpeg](https://ffmpeg.org/download.html#build-windows) e adicione os executáveis ao PATH. O Windows ainda não foi testado neste release. Os scripts não executam essas instalações por conta própria. Para builds específicos, configure `FFMPEG` e `FFPROBE` com o caminho do executável.

## Teste em dois minutos

Execute na pasta clonada:

```bash
python3 skills/video-craft/scripts/video_craft.py doctor
python3 skills/video-craft/scripts/video_craft.py demo out/teste.mp4
python3 skills/video-craft/scripts/video_craft.py sheet out/teste.mp4 out/contato.jpg
python3 skills/video-craft/scripts/video_craft.py verify out/teste.mp4 --require-audio --peak -2
```

O demo é uma **fixture sintética de quatro segundos**, com padrão de teste e tom de áudio. Serve para provar que o pipeline renderiza e mede; não representa o acabamento de uma peça editorial.

Para montar filmagem real, copie [timeline.json](skills/video-craft/assets/timeline.json) para seu projeto, substitua os arquivos e os tempos por trechos inspecionados e rode:

```bash
python3 skills/video-craft/scripts/video_craft.py assemble timeline.json out/corte.mp4
python3 skills/video-craft/scripts/video_craft.py inspect out/corte.mp4 --audio
```

A timeline aceita cortes, `keep`/`mute`, frame rate, dimensões e `contain`/`cover`. `contain` preserva o quadro; `cover` corta pelo centro. HDR sinalizado é recusado até passar por um tratamento de cor deliberado. A montagem não adiciona música nem legendas automaticamente.

## Som e entrega

Para uma mixagem completa pronta para normalizar:

```bash
python3 skills/video-craft/scripts/video_craft.py master out/mix.mp4 out/master.mp4
python3 skills/video-craft/scripts/video_craft.py verify out/master.mp4 --require-audio --lufs -14 --peak -2
```

`-14 LUFS` e `-2 dBTP` são padrões ajustáveis deste fluxo. A masterização mede o AAC depois do encode e só publica o arquivo se os alvos forem cumpridos. Entradas sem áudio, silenciosas ou que exijam ganho excessivo são recusadas. Uma versão com poucos sons e sem trilha deve preservar o silêncio, sem normalização de programa completo.

O pacote não certifica direitos autorais, acessibilidade, sincronização ou qualidade artística. Abra os frames, assista e ouça o export. Registre assets externos em [asset-sources.csv](skills/video-craft/assets/asset-sources.csv). **Arquivo renderizado, arquivo tecnicamente validado e peça revisada são estados diferentes.**

## Segurança e privacidade

Tudo roda localmente. Sem telemetria, chaves, upload automático, hooks ou `curl | sh`. Os scripts usam argumentos separados, recusam URLs de entrada, restringem protocolos de leitura e preservam arquivos existentes por padrão. Mídias e saídas são ignoradas pelo Git. Isso não anonimiza o conteúdo visual: revise antes de compartilhar.

Confira [SECURITY.md](SECURITY.md) para o escopo e as limitações. Para contribuir, leia [CONTRIBUTING.md](CONTRIBUTING.md). Os testes geram suas próprias mídias:

```bash
python3 -m unittest discover -s tests -v
```

## Licença e créditos

Código e documentação sob [MIT](LICENSE). Criação de Thiago Xikota. FFmpeg, Claude e Remotion são projetos/marcas de seus respectivos responsáveis; não estão incluídos nesta licença. Este projeto não é oficial nem afiliado à Anthropic, FFmpeg ou Remotion.

Se for útil no seu fluxo, uma estrela ajuda outras pessoas a encontrar o projeto. Exemplos reproduzíveis e correções também são bem-vindos.
