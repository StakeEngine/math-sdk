"""Handle symbol classes and initial generation."""


class SymbolDefinition:
    """Define symbol class object structure."""

    __slots__ = (
        "name",
        "special",
        "is_paying",
        "paytable",
        "special_flags",
    )

    def __init__(self, name, config, paytable):
        self.name = name

        self.special_flags = set()
        for prop, symbols in config.special_symbols.items():
            if name in symbols:
                self.special_flags.add(prop)

        self.special = bool(self.special_flags)

        if paytable:
            self.is_paying = True
            self.paytable = paytable
        else:
            self.is_paying = False
            self.paytable = None


class Symbol:
    """Symbol attributes must exist is __slots__ list."""

    __slots__ = (
        "defn",
        "explode",
        "locked",
        "scatter",
        "wild",
        "has_multiplier",
        "multiplier",
        "has_prize",
        "prize",
    )

    def __init__(self, defn: SymbolDefinition):
        self.defn = defn
        self.explode = False
        self.locked = False
        self.wild = False
        self.scatter = False
        self.multiplier = None
        self.prize = None
        self.assign_default_attribute()

    @property
    def name(self):
        """Get string symbol name."""
        return self.defn.name

    @property
    def is_special(self):
        """Is a special symbol."""
        return self.defn.special

    @property
    def special_flags(self):
        """Return all set special flags."""
        return self.defn.special_flags

    @property
    def is_wild(self):
        """Is a Wild/"""
        return self.defn.wild

    @property
    def is_scatter(self):
        """Is a Scatter."""
        return self.defn.scatter

    def check_attribute(self, *attrs):
        """Check if symbol attribute exists/is set."""
        for a in attrs:
            val = getattr(self, a, None)
            if val not in (None, False):
                return True
            if a in self.defn.special_flags:
                return True
        return False

    def get_attribute(self, attr):
        """Get attribute value (must exist)."""
        return getattr(self, attr)

    def assign_attribute(self, attribute_dict: dict) -> None:
        """Assign attribute value to symbol."""
        for prop, value in attribute_dict.items():
            setattr(self, prop, value)

    def assign_default_attribute(self):
        "Set inital __slots__ properties"
        for attr in self.defn.special_flags:
            match attr:
                case "scatter":
                    self.scatter = True
                case "wild":
                    self.wild = True
                case "multiplier":
                    self.has_multiplier = True
                    self.multiplier = 1
                case "prize":
                    self.has_prize = True
                    self.prize = 0


class SymbolStorage:
    """Initial symbol generation from configuration file."""

    def __init__(self, config: object, all_symbols: list):
        self.config = config
        paytable_by_symbol = {}
        for (kind, sym), val in config.paytable.items():
            paytable_by_symbol.setdefault(sym, []).append({str(kind): val})

        self.symbol_defs = {}
        for name in all_symbols:
            self.symbol_defs[name] = SymbolDefinition(
                name=name,
                config=config,
                paytable=paytable_by_symbol.get(name),
            )

    def create_symbol(self, name: str):
        """Create a new instance of symbol class."""
        try:
            return Symbol(self.symbol_defs[name])
        except KeyError:
            raise ValueError(f"Symbol '{name}' is not registered")
