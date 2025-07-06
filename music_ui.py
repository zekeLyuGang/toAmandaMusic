import os
import random
import shutil
from datetime import datetime
import gradio as gr

from setting import DEEPSEEK_KEY,SYSTEM_PROMPT,USER_PROMPT
from openai import OpenAI

MUSIC_DIR = "music"
PHOTO_DIR = "photo"
os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(PHOTO_DIR, exist_ok=True)
now = datetime.now()  # 获取当前日期和时间
cur_year, cur_month, cur_day = now.year, now.month, now.day
client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")


def get_sorted_music_files():
    """获取按字母顺序排序的音乐文件列表"""
    files = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(('.flac', '.mp3'))]
    return sorted(files, key=str.lower)


def get_daily_image():
    photos = [f for f in os.listdir(PHOTO_DIR) if os.path.isfile(os.path.join(PHOTO_DIR, f))]
    selected = random.choice(photos)
    return os.path.join(PHOTO_DIR, selected)


def get_daily_love_poetry():
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"{SYSTEM_PROMPT}"},
                {"role": "user", "content": f"今天是{cur_year}年，{cur_month}月，{cur_day}日，{USER_PROMPT}"},
            ],
            stream=False
        )
        current_poetry = response.choices[0].message.content.replace("\n", "<br>")  # 替换所有换行符
    except Exception as e:
        print(f"❌连接deepseek失败：{str(e)}")
        current_poetry = "不论晴空万里，还是乌云密布，我的心始终为你跳动~"
    return current_poetry

def on_page_load():
    new_poetry = get_daily_love_poetry()
    return f"### 今天是{cur_year}年{cur_month}月{cur_day}日,小刚刚想对小贝贝说:\n\n{new_poetry}"

def search_music_files(query):
    """搜索音乐文件"""
    if not query:
        return get_sorted_music_files()

    matched_files = []
    for file in get_sorted_music_files():
        if query.lower() in file.lower():
            matched_files.append(file)
    return matched_files


def upload_music(file):
    """上传音乐文件"""
    if file:
        filename = os.path.basename(file.name)
        dest_path = os.path.join(MUSIC_DIR, filename)
        shutil.move(file.name, dest_path)
        return get_sorted_music_files(), f"'{filename}' 上传成功！"
    return get_sorted_music_files(), "请选择要上传的文件"


def delete_selected_files(selected_files):
    """删除勾选的文件"""
    if not selected_files:
        return get_sorted_music_files(), "请先勾选要删除的文件"

    deleted = []
    for file in selected_files:
        os.remove(os.path.join(MUSIC_DIR, file))
        deleted.append(file)
    return get_sorted_music_files(), f"已删除: {', '.join(deleted)}"


def rename_music(filename, new_name):
    """重命名音乐文件"""
    if '.' in new_name:
        new_name = new_name.split('.')[0] + "." + filename.split('.')[1]
    else:
        new_name = new_name + "." + filename.split('.')[1]
    if filename and new_name:
        old_path = os.path.join(MUSIC_DIR, filename)
        new_path = os.path.join(MUSIC_DIR, new_name)
        os.rename(old_path, new_path)
        return gr.update(choices=get_sorted_music_files()), f"文件已从 {filename} 重命名为 {new_name}!"
    return gr.update(choices=get_sorted_music_files()), "请输入新文件名"


def download_music(filename):
    if not filename:
        return None
    file_path = os.path.join(MUSIC_DIR, filename)
    return file_path


def play_music(filename):
    """播放音乐"""
    if filename:
        return os.path.join(MUSIC_DIR, filename)
    return None


with gr.Blocks(title="toAmandaMusic") as demo:
    gr.Markdown("# 🎵 toAmandaMusic ❥(^_-)")
    with gr.Row():
        with gr.Column():
            image = gr.Image(label="可爱佩佩", value=get_daily_image, height=500)

        with gr.Column():
            cur_love_poetry = get_daily_love_poetry()
            poetry_display = gr.Markdown(f"""
            ### 今天是{cur_year}年{cur_month}月{cur_day}日,小刚刚正在想今天要对小佩佩说什么！",
          
            """, elem_classes="panel", height=500)

    # 监听页面加载事件
    demo.load(
        fn=on_page_load,
        outputs=poetry_display
    )

    with gr.Tab("播放音乐"):
        with gr.Row():
            search_play_box = gr.Textbox(
                label="搜索播放的音乐",
                placeholder="输入歌曲名关键词..."
            )
            search_play_btn = gr.Button("搜索", variant="primary")

        music_play_list = gr.Radio(
            label="选择要播放的音乐",
            choices=get_sorted_music_files(),
            interactive=True
        )
        play_btn = gr.Button("播放", variant="primary")
        audio_player = gr.Audio(label="播放器", interactive=False)
        download_btn = gr.Button("下载", variant="primary")

    with gr.Tab("上传音乐"):
        with gr.Row():
            file_upload = gr.File(label="选择音乐文件", file_types=["audio"])
            upload_btn = gr.Button("上传", variant="primary")
        upload_status = gr.Textbox(label="状态")

    with gr.Tab("管理音乐"):
        with gr.Row():
            # 搜索框
            search_box = gr.Textbox(
                label="输入关键字搜索",
                placeholder="输入歌曲名关键词..."
            )
            search_btn = gr.Button("搜索", variant="primary")

        # 显示搜索结果或全部文件
        music_manager_list = gr.Radio(
            label="音乐文件",
            choices=get_sorted_music_files(),
            interactive=True
        )
        with gr.Row():
            new_name_box = gr.Textbox(
                label="输入关新名字重命名",
                placeholder="输入新的名字"
            )
            rename_btn = gr.Button("重命名勾选的文件", variant="stop")
        # 删除按钮
        batch_delete_btn = gr.Button("删除勾选的文件", variant="stop")
        manage_status = gr.Textbox(label="操作状态")

    # 事件绑定
    upload_btn.click(
        upload_music,
        inputs=[file_upload],
        outputs=[music_manager_list, upload_status]
    )

    search_btn.click(
        fn=lambda query: gr.update(choices=search_music_files(query)),
        inputs=[search_box],
        outputs=[music_manager_list]
    )

    rename_btn.click(
        rename_music,
        inputs=[music_manager_list, new_name_box],
        outputs=[music_manager_list, manage_status]
    )

    search_play_btn.click(
        fn=lambda query: gr.update(choices=search_music_files(query)),
        inputs=[search_play_box],
        outputs=[music_play_list]
    )

    batch_delete_btn.click(
        delete_selected_files,
        inputs=[music_manager_list],
        outputs=[music_manager_list, manage_status]
    )

    play_btn.click(
        play_music,
        inputs=[music_play_list],
        outputs=[audio_player]
    )
    download_btn.click(
        fn=download_music,
        inputs=[music_play_list],
        outputs=gr.File(label="下载文件")  # 输出为文件类型，自动触发下载
    )


    # 更新所有音乐列表的通用函数
    def update_all_lists():
        files = get_sorted_music_files()
        return [
            gr.update(choices=files),  # 管理页列表
            gr.update(choices=files)  # 播放页列表
        ]


    # 当上传或删除操作后更新所有列表
    for btn in [upload_btn, batch_delete_btn]:
        btn.click(
            update_all_lists,
            outputs=[music_manager_list, music_play_list]
        )

if __name__ == "__main__":
    demo.launch(
        allowed_paths=["./photo"],
        server_name="0.0.0.0",
        server_port=8000
    )
