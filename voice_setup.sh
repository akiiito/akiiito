#!/bin/bash
# セリフ音声 (AivisSpeech Engine) と「同じ声チェック」用モデルの準備手順。課金なし・すべてローカル実行。
# 必要な許可ホスト: pkg-containers.githubusercontent.com, api.aivis-project.com, huggingface.co, us.aws.cdn.hf.co
# 1) ghcr.io/aivis-project/aivisspeech-engine:cpu-latest のレイヤーを取得して /opt/python と /opt/aivisspeech-engine に展開
# 2) エンジン起動 (初回に標準の声と日本語 BERT を自動取得):
#      cd /opt/aivisspeech-engine && .venv/bin/python run.py --host 127.0.0.1 --port 10101 --disable_sentry
# 3) 使う声を追加 (宗周定昌 / 阿井田 茂 / fumifumi。まお は標準で入る):
set -e
A=http://127.0.0.1:10101
for id in 00f29eb2-e12b-4f64-a5e8-4188be62de33 47e53151-a378-46f3-abee-ce13aa07feb1 71e72188-2726-4739-9aa9-39567396fb2a; do
  curl -s --noproxy '*' -X POST "$A/aivm_models/install" -F "url=https://api.aivis-project.com/v1/aivm-models/$id/download?model_type=AIVMX"
done
# 4) 話者照合モデル (make_reel.py の SPK_MODEL):
#      pip install onnxruntime kaldi-native-fbank
#      curl -L -o voxceleb_resnet34_LM.onnx https://huggingface.co/Wespeaker/wespeaker-voxceleb-resnet34-LM/resolve/main/voxceleb_resnet34_LM.onnx
