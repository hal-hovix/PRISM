./deploy/tailscale/README.md - v1.0.0

# Tailscale 接続手順 / How to connect via Tailscale

このアプリ自体は Tailscale へ依存しません。必要に応じてインフラ側でノード間接続を行ってください。

手順（概要）:

1. 管理者が Tailscale 管理画面でネットワークを作成
2. 各ホストに Tailscale クライアントをインストール
3. `tailscale up` で認証（鍵やIDはここに記載しないでください）
4. ACL で必要なポート (API: 8000, Web: 8080) の疎通を許可

# IP一覧
m1-hal-air: 100.89.157.36
iPhone173: 100.69.12.16
iPad163: 100.73.170.29

EOF ./deploy/tailscale/README.md - v1.0.0
# 修正履歴:
# - 2025-10-20 v1.0.0: 接続手順の最小説明

