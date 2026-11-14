# Kế hoạch tích hợp Agent-Reach

Mục tiêu: thêm các nguồn mà RSS không với tới (YouTube, GitHub search, web search, V2EX; sau đó Reddit/X) mà không đổi phần lọc, AI, lưu trữ và website.

## Kết quả thử thật (2026-11-14, cài trong venv riêng, chưa đụng repo)

| Kênh | Lệnh thử | Kết quả | Cần đăng nhập |
|---|---|---|---|
| github | `github search "agent skills"` | OK, có repo + ngày | Không |
| youtube | `youtube search "hackathon vietnam"` | OK, nhưng `published_at` = null | Không |
| web (Exa) | `web search "hackathon Vietnam 2026"` | OK, ra cả trang tổng hợp hackathon VN | Không |
| v2ex | `v2ex hot` | OK (tiếng Trung, ít liên quan) | Không |
| reddit | `reddit subreddit devops` | **Lỗi**: cần cài Node + OpenCLI (`agent-reach add reddit`) và đăng nhập | Có |
| twitter | `twitter search` | **Lỗi**: như trên | Có |
| Reddit RSS trực tiếp | `curl .../r/devops/top/.rss` | 200 từ máy này | Không |

Mọi kênh trả về cùng một dạng JSON: `items[] = {title, url, author, published_at, text, raw}`, nên chuyển được sang entry của pipeline bằng một hàm nhỏ.

## Cách ghép (nhỏ nhất)

Thêm một bước nguồn thứ hai bên cạnh RSS, **không** sửa `filters`, `llm`, `store`, `site`.

```
config/feeds.yaml      (RSS, như cũ)
config/reach.yaml      (MỚI: danh sách lệnh Agent-Reach)  ─┐
tech_news/reach.py     (MỚI: chạy CLI, đổi JSON → entry)   ├─▶ cùng danh sách entry ─▶ filters ─▶ llm ─▶ data/
tech_news/fetch.py     (gọi thêm reach.fetch_all)          ─┘
```

`reach.yaml` ví dụ (tên `source` quyết định danh mục qua bảng FORCED/DEFAULT như hiện nay):

```yaml
- {source: "YouTube: Claude Code", cmd: "youtube search 'claude code agent skills' --limit 5"}
- {source: "YouTube: Hackathon VN", cmd: "youtube search 'hackathon việt nam 2026' --limit 5"}
- {source: "GitHub Open Source",    cmd: "github search 'agent skills' --limit 5"}
- {source: "Google News: Hackathon", cmd: "web search 'hackathon Vietnam 2026' --limit 5"}
```

`reach.py` (~30 dòng): chạy `agent-reach <cmd>` bằng `subprocess` (timeout 90s, lỗi một lệnh thì bỏ qua như feed hỏng), đọc `items`, ánh xạ `title→title`, `url→link`, `text→description`, `published_at→date` (null thì dùng giờ hiện tại, bài sẽ qua cổng tuổi). Cài trong Actions: `pip install "git+https://github.com/Panniantong/Agent-Reach"` (không dùng bản PyPI cùng tên, đó là gói khác).

## Trạng thái

Giai đoạn 1 **đã code** (github, youtube, web hackathon): `tech_news/reach.py`, `config/reach.yaml`, bước cài trong `daily.yml`, 4 test. Chạy `--dry-run` thật: 25 bài thêm từ Agent-Reach, YouTube và web hackathon vào đúng danh mục. GitHub Search bị giới hạn 60 lượt/giờ khi không có token (đã thêm `GITHUB_TOKEN` trong workflow). Chưa chạy trên Actions.

## Các giai đoạn

1. **Giai đoạn 1: kênh không cần đăng nhập** (chạy được trên GitHub Actions): github, youtube, web, (v2ex nếu muốn).
   - Thêm `reach.py`, `reach.yaml`, test với dữ liệu mẫu, bước cài trong `daily.yml`.
   - Việc cần chú ý: `youtube` không có ngày đăng, nên cùng một video có thể quay lại mỗi ngày (dedup theo URL đã chặn lặp, nhưng không lọc được video cũ). Giảm nhẹ: dùng từ khoá có "2026", giữ `--limit` nhỏ.
   - `web search` dùng Exa, chưa rõ hạn mức miễn phí: đo trước khi để chạy hằng ngày.
2. **Giai đoạn 2: Reddit qua RSS công khai** (không cần Agent-Reach): thêm vài URL `.rss` vào `feeds.yaml`. Máy này trả 200, nhưng IP của GitHub Actions có thể bị Reddit chặn (403/429). Cần chạy thử một lần trên Actions rồi mới quyết định.
3. **Giai đoạn 3: X/Twitter và Reddit đăng nhập**: không chạy được trên Actions (cần Node, OpenCLI, trình duyệt và phiên đăng nhập sao chép từ Chrome). Nếu thật sự cần: một máy luôn bật (VPS nhỏ hoặc máy nhà) chạy `agent-reach` bằng cron, ghi cùng `data/*.jsonl` rồi `git push`. Dùng tài khoản phụ vì phiên đăng nhập được sao chép từ Chrome.

## Chi phí và rủi ro

- Chi phí hạ tầng vẫn $0. Chi phí AI tăng theo số bài mới (đã có trần `MAX_TOTAL=80`/ngày).
- Agent-Reach gọi đến nhiều công cụ bên thứ ba (`yt-dlp`, Exa, GitHub API); một công cụ hỏng thì chỉ mất nguồn đó, các nguồn khác vẫn chạy.
- Nên giữ `reach.yaml` ngắn (4–8 lệnh) để lượt chạy không dài và nhiễu không tăng.

## Cần bạn chọn trước khi tôi code

- Có làm giai đoạn 1 ngay không, và nguồn nào (đề xuất: github + youtube + web hackathon).
- Giai đoạn 3 có thật sự cần X/Reddit không (cần máy luôn bật).
