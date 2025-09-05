# TODO

## Improve Artist Detection

Fix the subscription extraction script to properly find music artists, video channels, etc. by:

- [ ] Search by name patterns
- [ ] Search by tags (separated by '|' character)
- [ ] Better DOM selectors for YouTube Music artist elements
- [ ] Distinguish between music artists vs video channels
- [ ] Handle different subscription types (artists, channels, podcasts)

Example format for artist detection:
```
Artist Name|music|artist
Channel Name|video|channel
Podcast Name|podcast|audio
```

Current issue: The extraction script picks up UI text instead of actual artist/channel names from subscriptions page.