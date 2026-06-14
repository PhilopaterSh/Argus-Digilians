import streamlit as st
import os
import time
import shutil
from datetime import datetime
from multi_agent_workflow import ProMultiAgentSystem, KNOWLEDGE_BASE_DIR, REPORTS_DIR, MEMORY_FILE

# إعدادات الصفحة
st.set_page_config(page_title="AI Multi-Agent Studio", page_icon="🤖", layout="wide")

# تصميم الواجهة
st.title("🤖 AI Multi-Agent Studio")
st.markdown("---")

# الشريط الجانبي
with st.sidebar:
    st.header("⚙️ إدارة الذاكرة")
    
    # 1. مسح الكاش التقني
    if st.button("🧹 مسح الذاكرة المؤقتة (Cache)", help="مسح ملفات النظام المؤقتة وتسريع الأداء"):
        st.cache_resource.clear()
        st.success("تم مسح الكاش التقني.")

    # 2. مسح سجل الجلسات
    if st.button("📜 مسح سجل المهام (Sessions)", help="سيقوم العميل بنسيان المهام السابقة تماماً"):
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
            st.success("تم مسح سجل الجلسات بنجاح.")
        else:
            st.info("لا يوجد سجل جلسات لمسحه.")

    # 3. مسح الملفات والتقارير
    if st.button("📂 مسح التقارير والمعرفة (Files)", help="حذف جميع ملفات Markdown والتقارير المخزنة"):
        deleted_count = 0
        for folder in [KNOWLEDGE_BASE_DIR, REPORTS_DIR]:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                            deleted_count += 1
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            deleted_count += 1
                    except Exception as e:
                        st.error(f"فشل حذف {file_path}: {e}")
        st.success(f"تم حذف {deleted_count} ملف/مجلد من التقارير والمعرفة.")

    st.markdown("---")
    st.info("النظام يعمل حالياً بمزيج من نماذج DeepSeek و Llama 3.3 لتوفير أقصى دقة.")

# مساحة الإدخال
task_input = st.text_area("أدخل المهمة أو سؤالك الاستراتيجي هنا:", placeholder="مثال: تحليل قواعد البيانات المسربة لعام 2026...")

if st.button("🚀 تشغيل العملاء"):
    if task_input:
        system = ProMultiAgentSystem()

        # حاوية لعرض حالة الوكلاء
        with st.status("⏳ العملاء يعملون الآن...", expanded=True) as status:
            st.write("🔍 جاري البحث في الويب والملفات المحلية...")
            local_info = system.local_rag_agent(task_input)
            web_info = system.researcher_agent(task_input)
            
            st.write("🕵️ جاري استقصاء الشبكة المظلمة (Dark Web)...")
            dark_info = system.darkweb_researcher_agent(task_input)
            
            combined_raw = f"LOCAL INFO:\n{local_info}\n\nWEB INFO:\n{web_info}\n\nDARK WEB INFO:\n{dark_info}"

            st.write("🧠 جاري التحليل الاستخباراتي...")
            system.state["task"] = task_input
            system.analyst_agent(combined_raw)

            st.write("⚖️ وكيل المعارضة: جاري فحص التضليل والفخاخ...")
            system.debater_agent(system.state["analysis"])

            st.write("✅ جاري تدقيق الحقائق وموازنة الآراء...")
            system.fact_checker_agent()

            st.write("🧐 جاري المراجعة النهائية للجودة...")
            while system.state["iterations"] < 2:
                feedback = system.reviewer_agent()
                if "APPROVED" in feedback.upper():
                    st.write("✅ تم اعتماد التحليل من قبل المراجع.")
                    break
                else:
                    st.write(f"⚠️ ملاحظة المراجع: {feedback}")
                    system.state["feedback"] = feedback
                    system.state["iterations"] += 1

            st.write("📝 جاري صياغة التقرير النهائي الموثق...")
            report = system.writer_agent()

            # حفظ التقرير وأرشفة الذاكرة
            system.save_report(report, time.time())
            system.memory_agent(report)

            status.update(label="✅ تم الانتهاء من المهمة بنجاح!", state="complete", expanded=False)

        # عرض التقرير النهائي
        st.markdown("### 📄 التقرير النهائي المعتمد")
        st.markdown(report)

        # زر لتحميل التقرير
        st.download_button(
            label="📥 تحميل التقرير (Markdown)",
            data=report,
            file_name=f"Report_{datetime.now().strftime('%H%M%S')}.md",
            mime="text/markdown",
        )
    else:
        st.warning("يرجى إدخال مهمة أولاً!")

# تذييل الصفحة
st.markdown("---")
st.caption("تم التطوير بواسطة Gemini CLI Agent - 2026")
