from playwright.sync_api import sync_playwright

prompt_answer = """# 角色设定
你是一个专业的前端开发工程师，同时也是一位资深的健康营养师。你精通HTML、CSS、JavaScript，并且深谙减脂餐的科学搭配原则。

# 任务目标
请根据我上传的食材清单以及PDF文件中的营养和个人健康信息，为我生成一个完整的、可交互的“减脂餐搭配网页”。

# 功能与交互要求
1. **食材与信息解析展示**：
   - 网页应清晰展示从PDF提取的关键营养指标和限制（如卡路里上限、忌口等）。
   - 以卡片或列表形式展示我上传的可用食材，并标注每种食材的预估热量和营养成分（蛋白质、脂肪、碳水）。

2. **交互式餐单生成与搭配**：
   - 提供一个可交互的配餐区域，用户可以通过点击或拖拽食材来组合一餐。
   - 实时计算并动态显示当前选中食材的总热量及宏量营养素比例，当超过目标热量时给出明显的视觉警告（如变红）。
   - 提供一个“一键推荐”按钮，利用JavaScript动态生成一套符合减脂标准的推荐食谱。

3. **UI/UX设计**：
   - 界面风格清新、健康（推荐绿色系）。
   - 确保完全的响应式设计，提供良好的PC和移动端体验。

# 约束条件
- 请输出包含HTML、CSS和JavaScript的完整单一HTML代码，确保可以直接在浏览器中打开运行。
- 代码中需包含完整的交互逻辑（如热量计算、食材选择等），不要省略或使用伪代码。
- 在复杂的计算和DOM操作逻辑处添加必要的中文注释。"""

def run():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9239")
        context = browser.contexts[0]
        page = context.pages[0]
        
        # Make sure we're operating on the right page
        for p_iter in context.pages:
            if "申请" in p_iter.content() or "资质审核" in p_iter.content():
                page = p_iter
                break
                
        # Wait for the modal / textarea to be visible
        textarea = page.locator("textarea").first
        if textarea.is_visible():
            print("Found textarea, filling it...")
            textarea.fill(prompt_answer)
            page.wait_for_timeout(1000)
            
            # Find submit button. It might be named "提交"
            submit_btn = page.get_by_role("button", name="提交", exact=True)
            if submit_btn.is_visible():
                print("Clicking submit...")
                submit_btn.click()
                page.wait_for_timeout(3000)
                page.screenshot(path="after_submit.png")
                print("Submitted. Saved screenshot to after_submit.png")
            else:
                print("Submit button not found.")
        else:
            print("Textarea not visible.")
            
        browser.close()

if __name__ == "__main__":
    run()