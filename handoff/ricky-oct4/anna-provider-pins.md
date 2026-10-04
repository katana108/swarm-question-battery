# Serving-provider pins for Anna

Recovered from the saved broad-screen baseline response metadata and checked against OpenRouter public endpoint listings on October 4. These identify serving providers, not model makers. Luna judging calls are excluded.

| Model ID | Logged serving provider | Provider pin |
|---|---|---|
| z-ai/glm-5.3 | Decart | decart/fp4 |
| anthropic/claude-opus-4.8 | Claude Platform on AWS | claude-on-aws |
| openai/gpt-5.5 | OpenAI | openai |
| x-ai/grok-4.6 | xAI | xai |
| z-ai/glm-5.2 | Mistral | mistral |
| anthropic/claude-opus-4.7 | Claude Platform on AWS | claude-on-aws |
| openai/gpt-5.4 | OpenAI | openai |
| x-ai/grok-4.5 | xAI | xai |
| deepseek/deepseek-v4-pro | Relace | relace/fp4 |
| deepseek/deepseek-v4-pro-0813 | Relace | relace/fp4 |
| moonshotai/kimi-k2.7-code | Inceptron | inceptron/int4 |
| moonshotai/kimi-k3 | Several within the same baseline trial | unresolved |

Use provider.only=[pin] and provider.allow_fallbacks=false in the raw OpenRouter request. Base pins openai, xai, and mistral lock the provider family but do not prove identity with yesterday’s regional/service-tier endpoint. Logs recorded provider display names, not exact endpoint tags. Mistral currently lists mistral/zdr and mistral/eu. OpenAI lists openai, openai/fast, openai/flex; xAI has several regional/priority variants. Narrow to one tag if endpoint-level identity is required, recording that choice separately.

Kimi K3’s baseline switched among InferenceNet, Wafer, Together, Phala, and Parasail. Candidate pins currently listed: inference-net/fp4, inference-net/fast, wafer, wafer/us, together, phala, parasail/fp4. There is no unique yesterday endpoint to reproduce. Choose one explicitly before a pinned trial; do not claim exact endpoint continuity for reused mixed-provider data.

Quantization is explicit in several endpoint tags (fp4/int4). Preserve these tags as protocol metadata.

Existing broad trials and currently launched main-model n=3 sweep were not provider-pinned. Do not relabel them as pinned data. If Anna pins her run, annotate that routing change when comparing or sharing baselines.

Evidence: outputs/baseline-serving-providers.json and outputs/serving-provider-endpoint-lookup.json. Routing reference: https://openrouter.ai/docs/guides/routing/provider-selection
