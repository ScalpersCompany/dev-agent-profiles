# Profile skills

This profile ships no domain skill. Its mechanism is the role contract in `roles.json`, and the
kit's rule is that a skill is written after an observed failure, not before it. When a role
fails in a way the contract cannot catch, the fix becomes a rule here or in
`gga/REVIEW-RULES.md`; a skill is added only when the failure is a procedure the agent has to
learn, and it is added with its eval case.
