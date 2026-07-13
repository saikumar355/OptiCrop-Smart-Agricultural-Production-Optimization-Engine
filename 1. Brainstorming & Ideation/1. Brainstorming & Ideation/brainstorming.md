# Brainstorming & Ideation — OptiCrop AI

## Problem Statement

Farmers and agronomists lack data-driven tools to decide which crop to plant based on their specific soil chemistry and local climate conditions. Poor crop selection leads to low yields, wasted resources, and economic loss.

## Core Idea

Build an AI-powered platform that:
- Takes 7 measurable soil and climate inputs from the farmer
- Runs them through a trained ML model
- Returns the optimal crop recommendation with a confidence score
- Also provides threshold-based suitability analysis for all supported crops

## Why This Problem?

- Agriculture employs 40%+ of the global workforce
- Crop failure due to wrong selection is preventable with data
- Soil testing labs produce exactly the inputs our model needs (N, P, K, pH)
- Weather APIs can supply temperature, humidity, rainfall

## Initial Ideas Explored

| Idea | Decision |
|---|---|
| Single ML algorithm | Rejected — compare 9 algorithms, pick best by F1 |
| Rule-based system only | Too rigid — use ML for recommendation, rules for suitability |
| Mobile app | Out of scope — web platform first |
| Real-time soil sensor integration | Future feature — CSV input for now |
| Cloud database (PostgreSQL) | Overkill for v1 — SQLite is sufficient |
| User accounts / multi-tenant | Out of scope — single admin model |

## Target Users

1. **Farmers** — get crop recommendations for their land
2. **Agronomists** — evaluate suitability across multiple crops
3. **Agricultural administrators** — monitor system, manage model

## Key Decisions

- **7 input features** — N, P, K, Temperature, Humidity, Rainfall, pH (standard soil test outputs)
- **22 crop classes** — covers major crops across tropical and subtropical regions
- **ExtraTrees won** with F1-weighted = 0.93 on the Kaggle crop recommendation dataset
- **Flask backend** — lightweight, Python-native, easy to deploy
- **SQLite** — zero-config database, sufficient for single-server deployment
- **Property-based testing** — formal correctness guarantees using Hypothesis

## Dataset

Kaggle Crop Recommendation Dataset
- 2,200 rows, 8 columns (7 features + label)
- 22 balanced crop classes, 100 samples each
- Source: https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset
