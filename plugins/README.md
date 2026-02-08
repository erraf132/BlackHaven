# BlackHaven Plugins

Drop Python files into `~/.blackhaven/plugins` that expose `get_module()` returning:

```
{
  "name": "Module Name",
  "description": "What it does",
  "run": callable,
}
```

They will be loaded at runtime alongside core modules.
