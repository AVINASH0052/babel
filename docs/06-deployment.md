# Deployment

## Local Development

```bash
# Single document processing
babelextreme translate input.pdf --output output.pdf \
    --source-lang ja --target-lang en \
    --config config.yaml
```

---

## Production (Batch Processing)

```yaml
# docker-compose.yml
services:
  orchestrator:
    image: babelextreme/orchestrator:latest
    environment:
      - REDIS_URL=redis://redis:6379
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./input:/input
      - ./output:/output
      
  extraction-worker:
    image: babelextreme/extraction:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
              
  translation-worker:
    image: babelextreme/translation:latest
    
  reconstruction-worker:
    image: babelextreme/reconstruction:latest
```

---

## Getting Started

### Quick Validation (5 minutes)

1. **Test MinerU extraction** on a single complex page:
   ```bash
   pip install magic-pdf
   magic-pdf -p input.pdf -o output/
   ```

2. **Check the output `output.md`**:
   - Are formulas in LaTeX? ✓
   - Are tables structured? ✓
   - Are images separated? ✓

3. **If extraction works**, the rest is straightforward translation + assembly.

---

## Next Implementation Steps

1. [ ] Set up project structure and dependencies
2. [ ] Implement Stage 1 (Ingestion) with tests
3. [ ] Integrate MinerU for Stage 2 (Extraction)
4. [ ] Build translation prompts for Stage 3
5. [ ] Implement Typst reconstruction for Stage 4
6. [ ] End-to-end integration testing
7. [ ] Benchmark against BabelDOC on sample documents
