"use client";

import { useRef, useState } from "react";

type RenameItem = {
  handle: FileSystemFileHandle;
  from: string;
  to: string;
  status: "待处理" | "已完成" | "跳过" | "失败";
  message?: string;
};

type DirectoryPickerWindow = Window & {
  showDirectoryPicker?: () => Promise<FileSystemDirectoryHandle>;
};

export default function Home() {
  const [folderName, setFolderName] = useState("");
  const [items, setItems] = useState<RenameItem[]>([]);
  const [notice, setNotice] = useState("");
  const [isRenaming, setIsRenaming] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const prepareItems = async (directory: FileSystemDirectoryHandle) => {
    const nextItems: RenameItem[] = [];
    for await (const [, handle] of directory.entries()) {
      if (handle.kind !== "file") continue;
      const to = handle.name.replace(/[a-z]/g, (letter) => letter.toUpperCase());
      if (to !== handle.name) {
        nextItems.push({ handle, from: handle.name, to, status: "待处理" });
      }
    }
    setFolderName(directory.name);
    setItems(nextItems);
    setNotice(nextItems.length ? `已找到 ${nextItems.length} 个需要改名的文件。` : "这个文件夹里的文件名已经全部符合要求。 ");
  };

  const selectFolder = async () => {
    setNotice("");
    try {
      const picker = window as DirectoryPickerWindow;
      if (!picker.showDirectoryPicker) {
        fileInputRef.current?.click();
        return;
      }
      const directory = await picker.showDirectoryPicker();
      await prepareItems(directory);
    } catch (error) {
      if ((error as DOMException).name !== "AbortError") setNotice("无法读取该文件夹，请再试一次。");
    }
  };

  const renameAll = async () => {
    setIsRenaming(true);
    let completed = 0;
    const updated = [...items];
    for (let index = 0; index < updated.length; index += 1) {
      const item = updated[index];
      try {
        const permission = await item.handle.requestPermission({ mode: "readwrite" });
        if (permission !== "granted") {
          updated[index] = { ...item, status: "跳过", message: "未获得修改权限" };
        } else {
          await item.handle.move(item.to);
          updated[index] = { ...item, status: "已完成" };
          completed += 1;
        }
      } catch (error) {
        updated[index] = { ...item, status: "失败", message: error instanceof Error ? error.message : "改名失败" };
      }
      setItems([...updated]);
    }
    setIsRenaming(false);
    setNotice(`处理完成：${completed} 个文件已改名。`);
  };

  return (
    <main className="page-shell">
      <input
        ref={fileInputRef}
        className="visually-hidden"
        type="file"
        // @ts-expect-error webkitdirectory is supported by Chromium-based browsers.
        webkitdirectory=""
        multiple
        onChange={() => setNotice("请使用最新版 Chrome 或 Edge 打开本工具，以便直接修改文件名。")}
      />
      <section className="hero">
        <p className="eyebrow">本地文件整理工具</p>
        <h1>文件名大写转换</h1>
        <p className="intro">一键将文件名中的小写英文字母改成大写；数字、中文、空格、符号和扩展名中的其他字符都保持原样。</p>
      </section>

      <section className="tool-card" aria-label="文件夹改名工具">
        <div className="card-heading">
          <div>
            <p className="step">第 1 步</p>
            <h2>选择文件夹</h2>
          </div>
          {folderName && <span className="folder-tag">{folderName}</span>}
        </div>
        <button className="select-button" onClick={selectFolder} disabled={isRenaming}>
          选择文件夹
        </button>
        <p className="privacy-note">文件只在你的电脑上处理，不会上传到服务器。仅处理当前文件夹内的文件，不会进入子文件夹。</p>

        {notice && <p className="notice" role="status">{notice}</p>}

        {items.length > 0 && (
          <div className="results">
            <div className="results-header">
              <div>
                <p className="step">第 2 步</p>
                <h2>确认改名</h2>
              </div>
              <button className="rename-button" onClick={renameAll} disabled={isRenaming}>
                {isRenaming ? "正在改名…" : `确认改名 ${items.length} 个文件`}
              </button>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>原文件名</th><th>改为</th><th>状态</th></tr></thead>
                <tbody>{items.map((item, index) => <tr key={`${item.from}-${index}`}><td>{item.from}</td><td>{item.to}</td><td><span className={`status status-${item.status}`}>{item.status}{item.message ? `：${item.message}` : ""}</span></td></tr>)}</tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      <section className="rules" aria-label="改名规则">
        <p>例如：<strong>report-final_v2.docx</strong> → <strong>REPORT-FINAL_V2.DOCX</strong></p>
      </section>
    </main>
  );
}
