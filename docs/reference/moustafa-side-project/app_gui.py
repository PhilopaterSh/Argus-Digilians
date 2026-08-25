import streamlit as st
import os
import time
import shutil
from datetime import datetime
from multi_agent_workflow import ProMultiAgentSystem, KNOWLEDGE_BASE_DIR, REPORTS_DIR, MEMORY_FILE

# ╪Ñ╪╣╪»╪º╪»╪º╪¬ ╪º┘ä╪╡┘ü╪¡╪⌐
st.set_page_config(page_title="AI Multi-Agent Studio", page_icon="≡ƒñû", layout="wide")

# ╪¬╪╡┘à┘è┘à ╪º┘ä┘ê╪º╪¼┘ç╪⌐
st.title("≡ƒñû AI Multi-Agent Studio")
st.markdown("---")

# ╪º┘ä╪┤╪▒┘è╪╖ ╪º┘ä╪¼╪º┘å╪¿┘è
with st.sidebar:
    st.header("ΓÜÖ∩╕Å ╪Ñ╪»╪º╪▒╪⌐ ╪º┘ä╪░╪º┘â╪▒╪⌐")
    
    # 1. ┘à╪│╪¡ ╪º┘ä┘â╪º╪┤ ╪º┘ä╪¬┘é┘å┘è
    if st.button("≡ƒº╣ ┘à╪│╪¡ ╪º┘ä╪░╪º┘â╪▒╪⌐ ╪º┘ä┘à╪ñ┘é╪¬╪⌐ (Cache)", help="┘à╪│╪¡ ┘à┘ä┘ü╪º╪¬ ╪º┘ä┘å╪╕╪º┘à ╪º┘ä┘à╪ñ┘é╪¬╪⌐ ┘ê╪¬╪│╪▒┘è╪╣ ╪º┘ä╪ú╪»╪º╪í"):
        st.cache_resource.clear()
        st.success("╪¬┘à ┘à╪│╪¡ ╪º┘ä┘â╪º╪┤ ╪º┘ä╪¬┘é┘å┘è.")

    # 2. ┘à╪│╪¡ ╪│╪¼┘ä ╪º┘ä╪¼┘ä╪│╪º╪¬
    if st.button("≡ƒô£ ┘à╪│╪¡ ╪│╪¼┘ä ╪º┘ä┘à┘ç╪º┘à (Sessions)", help="╪│┘è┘é┘ê┘à ╪º┘ä╪╣┘à┘è┘ä ╪¿┘å╪│┘è╪º┘å ╪º┘ä┘à┘ç╪º┘à ╪º┘ä╪│╪º╪¿┘é╪⌐ ╪¬┘à╪º┘à╪º┘ï"):
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
            st.success("╪¬┘à ┘à╪│╪¡ ╪│╪¼┘ä ╪º┘ä╪¼┘ä╪│╪º╪¬ ╪¿┘å╪¼╪º╪¡.")
        else:
            st.info("┘ä╪º ┘è┘ê╪¼╪» ╪│╪¼┘ä ╪¼┘ä╪│╪º╪¬ ┘ä┘à╪│╪¡┘ç.")

    # 3. ┘à╪│╪¡ ╪º┘ä┘à┘ä┘ü╪º╪¬ ┘ê╪º┘ä╪¬┘é╪º╪▒┘è╪▒
    if st.button("≡ƒôé ┘à╪│╪¡ ╪º┘ä╪¬┘é╪º╪▒┘è╪▒ ┘ê╪º┘ä┘à╪╣╪▒┘ü╪⌐ (Files)", help="╪¡╪░┘ü ╪¼┘à┘è╪╣ ┘à┘ä┘ü╪º╪¬ Markdown ┘ê╪º┘ä╪¬┘é╪º╪▒┘è╪▒ ╪º┘ä┘à╪«╪▓┘å╪⌐"):
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
                        st.error(f"┘ü╪┤┘ä ╪¡╪░┘ü {file_path}: {e}")
        st.success(f"╪¬┘à ╪¡╪░┘ü {deleted_count} ┘à┘ä┘ü/┘à╪¼┘ä╪» ┘à┘å ╪º┘ä╪¬┘é╪º╪▒┘è╪▒ ┘ê╪º┘ä┘à╪╣╪▒┘ü╪⌐.")

    st.markdown("---")
    st.info("╪º┘ä┘å╪╕╪º┘à ┘è╪╣┘à┘ä ╪¡╪º┘ä┘è╪º┘ï ╪¿┘à╪▓┘è╪¼ ┘à┘å ┘å┘à╪º╪░╪¼ DeepSeek ┘ê Llama 3.3 ┘ä╪¬┘ê┘ü┘è╪▒ ╪ú┘é╪╡┘ë ╪»┘é╪⌐.")

# ┘à╪│╪º╪¡╪⌐ ╪º┘ä╪Ñ╪»╪«╪º┘ä
task_input = st.text_area("╪ú╪»╪«┘ä ╪º┘ä┘à┘ç┘à╪⌐ ╪ú┘ê ╪│╪ñ╪º┘ä┘â ╪º┘ä╪º╪│╪¬╪▒╪º╪¬┘è╪¼┘è ┘ç┘å╪º:", placeholder="┘à╪½╪º┘ä: ╪¬╪¡┘ä┘è┘ä ┘é┘ê╪º╪╣╪» ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ╪º┘ä┘à╪│╪▒╪¿╪⌐ ┘ä╪╣╪º┘à 2026...")

if st.button("≡ƒÜÇ ╪¬╪┤╪║┘è┘ä ╪º┘ä╪╣┘à┘ä╪º╪í"):
    if task_input:
        system = ProMultiAgentSystem()

        # ╪¡╪º┘ê┘è╪⌐ ┘ä╪╣╪▒╪╢ ╪¡╪º┘ä╪⌐ ╪º┘ä┘ê┘â┘ä╪º╪í
        with st.status("ΓÅ│ ╪º┘ä╪╣┘à┘ä╪º╪í ┘è╪╣┘à┘ä┘ê┘å ╪º┘ä╪ó┘å...", expanded=True) as status:
            st.write("≡ƒöì ╪¼╪º╪▒┘è ╪º┘ä╪¿╪¡╪½ ┘ü┘è ╪º┘ä┘ê┘è╪¿ ┘ê╪º┘ä┘à┘ä┘ü╪º╪¬ ╪º┘ä┘à╪¡┘ä┘è╪⌐...")
            local_info = system.local_rag_agent(task_input)
            web_info = system.researcher_agent(task_input)
            
            st.write("≡ƒò╡∩╕Å ╪¼╪º╪▒┘è ╪º╪│╪¬┘é╪╡╪º╪í ╪º┘ä╪┤╪¿┘â╪⌐ ╪º┘ä┘à╪╕┘ä┘à╪⌐ (Dark Web)...")
            dark_info = system.darkweb_researcher_agent(task_input)
            
            combined_raw = f"LOCAL INFO:\n{local_info}\n\nWEB INFO:\n{web_info}\n\nDARK WEB INFO:\n{dark_info}"

            st.write("≡ƒºá ╪¼╪º╪▒┘è ╪º┘ä╪¬╪¡┘ä┘è┘ä ╪º┘ä╪º╪│╪¬╪«╪¿╪º╪▒╪º╪¬┘è...")
            system.state["task"] = task_input
            system.analyst_agent(combined_raw)

            st.write("ΓÜû∩╕Å ┘ê┘â┘è┘ä ╪º┘ä┘à╪╣╪º╪▒╪╢╪⌐: ╪¼╪º╪▒┘è ┘ü╪¡╪╡ ╪º┘ä╪¬╪╢┘ä┘è┘ä ┘ê╪º┘ä┘ü╪«╪º╪«...")
            system.debater_agent(system.state["analysis"])

            st.write("Γ£à ╪¼╪º╪▒┘è ╪¬╪»┘é┘è┘é ╪º┘ä╪¡┘é╪º╪ª┘é ┘ê┘à┘ê╪º╪▓┘å╪⌐ ╪º┘ä╪ó╪▒╪º╪í...")
            system.fact_checker_agent()

            st.write("≡ƒºÉ ╪¼╪º╪▒┘è ╪º┘ä┘à╪▒╪º╪¼╪╣╪⌐ ╪º┘ä┘å┘ç╪º╪ª┘è╪⌐ ┘ä┘ä╪¼┘ê╪»╪⌐...")
            while system.state["iterations"] < 2:
                feedback = system.reviewer_agent()
                if "APPROVED" in feedback.upper():
                    st.write("Γ£à ╪¬┘à ╪º╪╣╪¬┘à╪º╪» ╪º┘ä╪¬╪¡┘ä┘è┘ä ┘à┘å ┘é╪¿┘ä ╪º┘ä┘à╪▒╪º╪¼╪╣.")
                    break
                else:
                    st.write(f"ΓÜá∩╕Å ┘à┘ä╪º╪¡╪╕╪⌐ ╪º┘ä┘à╪▒╪º╪¼╪╣: {feedback}")
                    system.state["feedback"] = feedback
                    system.state["iterations"] += 1

            st.write("≡ƒô¥ ╪¼╪º╪▒┘è ╪╡┘è╪º╪║╪⌐ ╪º┘ä╪¬┘é╪▒┘è╪▒ ╪º┘ä┘å┘ç╪º╪ª┘è ╪º┘ä┘à┘ê╪½┘é...")
            report = system.writer_agent()

            # ╪¡┘ü╪╕ ╪º┘ä╪¬┘é╪▒┘è╪▒ ┘ê╪ú╪▒╪┤┘ü╪⌐ ╪º┘ä╪░╪º┘â╪▒╪⌐
            system.save_report(report, time.time())
            system.memory_agent(report)

            status.update(label="Γ£à ╪¬┘à ╪º┘ä╪º┘å╪¬┘ç╪º╪í ┘à┘å ╪º┘ä┘à┘ç┘à╪⌐ ╪¿┘å╪¼╪º╪¡!", state="complete", expanded=False)

        # ╪╣╪▒╪╢ ╪º┘ä╪¬┘é╪▒┘è╪▒ ╪º┘ä┘å┘ç╪º╪ª┘è
        st.markdown("### ≡ƒôä ╪º┘ä╪¬┘é╪▒┘è╪▒ ╪º┘ä┘å┘ç╪º╪ª┘è ╪º┘ä┘à╪╣╪¬┘à╪»")
        st.markdown(report)

        # ╪▓╪▒ ┘ä╪¬╪¡┘à┘è┘ä ╪º┘ä╪¬┘é╪▒┘è╪▒
        st.download_button(
            label="≡ƒôÑ ╪¬╪¡┘à┘è┘ä ╪º┘ä╪¬┘é╪▒┘è╪▒ (Markdown)",
            data=report,
            file_name=f"Report_{datetime.now().strftime('%H%M%S')}.md",
            mime="text/markdown",
        )
    else:
        st.warning("┘è╪▒╪¼┘ë ╪Ñ╪»╪«╪º┘ä ┘à┘ç┘à╪⌐ ╪ú┘ê┘ä╪º┘ï!")

# ╪¬╪░┘è┘è┘ä ╪º┘ä╪╡┘ü╪¡╪⌐
st.markdown("---")
st.caption("╪¬┘à ╪º┘ä╪¬╪╖┘ê┘è╪▒ ╪¿┘ê╪º╪│╪╖╪⌐ Gemini CLI Agent - 2026")
