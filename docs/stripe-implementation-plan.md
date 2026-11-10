# Stripe implementation plan

Status: Checkout, Customer Portal and a webhook already exist in `app.py` (around line 4178), driven by `plans.py`. This plan covers what's left to make it production-safe. Target API version is 2026-10-28.endive and the Python SDK is `stripe` 16.0.0.

## What exists

Subscription Checkout with inline `price_data`, a portal session endpoint, `/api/billing`, and a hand-verified `/stripe/webhook` handling `checkout.session.completed` plus `customer.subscription.updated/deleted`. Tier changes go through `_set_user_tier`, founders are exempt, and automatic tax is behind `STRIPE_AUTOMATIC_TAX=1`.

## Gaps, in priority order

1. Webhook coverage. Missing `invoice.paid`, `invoice.payment_failed`, `checkout.session.async_payment_succeeded`, `charge.refunded`, `charge.dispute.created` and `radar.early_fraud_warning.created`. Renewals, failed payments, refunds and disputes are currently invisible. Subscribe only to events the handler acts on.
2. User mapping. Events resolve to a user through `metadata.username`. Store `customer_id` and `subscription_id` on the user (already in `profile.billing`) and look the user up by those, with metadata as fallback only. Refund and dispute events carry no metadata, so they need this lookup anyway.
3. Idempotency. Persist processed `event.id`s (a small Postgres table) and skip repeats; Stripe retries.
4. Period end. On current API versions `current_period_end` lives on the subscription item, not the subscription. Read `item["current_period_end"]`, otherwise the billing page's renewal date will be empty.
5. Persistent catalog. Replace inline `price_data` with one Product per plan (Beginner, Pro), each with a monthly and annual Price, found by `lookup_key`. Inline prices create a new throwaway product per checkout and stop the portal offering plan switching.
6. SDK. Add `stripe` to `requirements.txt`, create a `StripeClient`, drop the `requests` wrapper and `_stripe_signature_ok`, verify with `client.construct_event`. Pin the API version.
7. Checkout tagging. Pass `integration_identifier` (a label plus 8 random letters) on `checkout.sessions.create`.
8. Keys. Use a restricted key (`rk_`) with only Checkout Sessions, Customers, Portal and Subscriptions permissions, not `sk_`.
9. Tax. Create registrations in the Dashboard before setting `STRIPE_AUTOMATIC_TAX=1`, otherwise Stripe collects no tax and raises no error. Decide inclusive or exclusive pricing and whether to bill in USD only.
10. Portal config. Enable cancel at period end, payment method update, invoice history and plan switching between the two Products.
11. Tests. Webhook tests in `tests/` using signed fixture payloads: upgrade, renewal, failed payment, cancel, refund, duplicate event.

## Rollout

Develop against its own Stripe sandbox (`stripe sandbox create`), with `stripe listen --forward-to localhost:5000/stripe/webhook` for local events. Set `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` on Railway for the sandbox first, run through the test cards, then swap in live keys and a live webhook endpoint. Walk the Stripe go-live checklist before switching.

## Educational framing

Pricing copy sells access to education and tools. Keep plan blurbs and receipts descriptive ("Full Backtester and Signals suite"), never outcome claims.
