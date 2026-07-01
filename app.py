"""
Streamlit Sandbox App for Redrob Ranker.

"""
import streamlit as st
import json
import csv
import io
import time
import tempfile
import os

st.set_page_config(
    page_title="Redrob Candidate Ranker",
    page_icon="🎯",
    layout="wide",
)


def main():
    st.title("Redrob Candidate Ranker")
    st.markdown(
        "Upload a candidate JSON/JSONL file (≤100 candidates) to see the "
        "ranking system in action. This sandbox validates that the ranker "
        "runs end-to-end and produces a valid CSV."
    )

    
    # File upload
    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded = st.file_uploader(
            "Upload candidate file",
            type=["json", "jsonl"],
            help="Accepts .json (array) or .jsonl (one JSON per line)",
        )
        save_to_disk = st.checkbox("Save output to output/ directory", value=True)

    with col2:
        top_n = st.number_input(
            "Top N candidates to rank",
            min_value=1,
            max_value=100,
            value=100,
            help="How many top candidates to include in output",
        )
        filename_input = st.text_input("Output Filename", value="team_Tech Elites.csv")
        validate_output = st.checkbox("Validate Submission CSV", value=True)

    if uploaded is not None:
        content = uploaded.read().decode("utf-8")

        # Parse candidates
        try:
            if uploaded.name.endswith(".json"):
                candidates = json.loads(content)
                if not isinstance(candidates, list):
                    candidates = [candidates]
            else:
                candidates = [
                    json.loads(line)
                    for line in content.strip().split("\n")
                    if line.strip()
                ]
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
            return

        st.success(f" Loaded {len(candidates)} candidates from `{uploaded.name}`")

        if st.button(" Run Ranker", type="primary", use_container_width=True):
            start_time = time.time()

            # Write to temp file for the ranker
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
            ) as f:
                for c in candidates:
                    f.write(json.dumps(c) + "\n")
                temp_path = f.name

            try:
                # Import and run ranker
                with st.spinner("Scoring candidates..."):
                    from src.ranker import rank_candidates
                    from src.reasoning import generate_reasoning

                    top = rank_candidates(
                        temp_path,
                        top_n=min(len(candidates), top_n),
                        show_progress=False,
                    )

                    for entry in top:
                        entry["reasoning"] = generate_reasoning(entry)

                elapsed = time.time() - start_time

                st.success(
                    f"Ranked {len(top)} candidates in {elapsed:.2f}s"
                )

                # Show timing
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Candidates Ranked", len(top))
                col_b.metric("Runtime", f"{elapsed:.2f}s")
                col_c.metric("Budget Used", f"{elapsed / 300 * 100:.1f}%")

                st.divider()

                # Display results
                st.subheader(" Ranked Candidates")

                for entry in top:
                    comp = entry.get("components", {})
                    with st.expander(
                        f"**Rank {entry['rank']}** — "
                        f"`{entry['candidate_id']}` — "
                        f"Score: {entry['score']:.4f}"
                    ):
                        st.markdown(f"> {entry['reasoning']}")

                        # Show component scores
                        if comp:
                            score_cols = st.columns(len(comp))
                            for i, (key, val) in enumerate(comp.items()):
                                score_cols[i].metric(
                                    key.replace("_", " ").title(),
                                    f"{val:.2f}",
                                )

                st.divider()

                # Download CSV
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["candidate_id", "rank", "score", "reasoning"])
                for entry in top:
                    writer.writerow([
                        entry["candidate_id"],
                        entry["rank"],
                        f"{entry['score']:.4f}",
                        entry["reasoning"],
                    ])

                csv_data = output.getvalue()

                st.download_button(
                    " Download Submission CSV",
                    csv_data,
                    file_name=filename_input,
                    mime="text/csv",
                    use_container_width=True,
                )

                if save_to_disk:
                    out_path = os.path.join("output", filename_input)
                    os.makedirs("output", exist_ok=True)
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(csv_data)
                    st.success(f" Saved CSV to `{out_path}`")

                    if validate_output:
                        try:
                            from validate_submission import validate_submission
                            errors = validate_submission(out_path)
                            if errors:
                                st.error(f" Validation failed ({len(errors)} issues):")
                                for e in errors:
                                    st.error(f"- {e}")
                            else:
                                st.success(" Validation passed! CSV is valid for submission.")
                        except ImportError as e:
                            st.warning(f"Could not import validation module: {e}")

            finally:
                os.unlink(temp_path)

    else:
        # Show instructions when no file uploaded
        st.info(
            "Upload a candidate file to get started. "
        )

        st.markdown("""
        ### How It Works

        1. **Upload** a candidate JSON/JSONL file (≤100 candidates)
        2. **Click** "Run Ranker" to score and rank candidates
        3. **Review** the ranked results with component score breakdowns
        4. **Download** the submission CSV

        ### Scoring Components

        | Component | Weight | What It Measures |
        |-----------|--------|------------------|
        | Title Relevance | 25% | How well the current title matches AI/ML engineering |
        | Skill Match | 20% | Overlap with must-have and nice-to-have skills |
        | Career Trajectory | 25% | Product company experience, production ML work |
        | Experience Fit | 10% | Years of experience vs 5-9 year target |
        | Location | 5% | Proximity to Pune/Noida |
        | Education | 5% | Tier and field relevance |
        | Behavioral | 10% | Engagement, responsiveness, availability |
        """)


if __name__ == "__main__":
    main()
