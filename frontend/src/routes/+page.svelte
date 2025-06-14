<!-- 
  File: frontend/src/routes/+page.svelte
  Description: Revised version of the Blonderabbit Cluster Game. 
  This version fixes the spin mechanism and implements a more compact, streamlined UI.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import * as PIXI from 'pixi.js';
  import { gsap } from 'gsap';
  import { PixiPlugin } from 'gsap/PixiPlugin';

  // --- GSAP and PixiJS Initialization ---
  gsap.registerPlugin(PixiPlugin);
  PixiPlugin.registerPIXI(PIXI);

  // --- Game Configuration (Slimmer UI) ---
  const GRID_WIDTH = 7;
  const GRID_HEIGHT = 7;
  const SYMBOL_SIZE = 70; // Reduced size for a tighter grid
  const PADDING = 10;
  const API_URL = 'http://localhost:5000/play';

  // --- Asset Mapping ---
  const assetPaths = {
    GF: '/golden_fleece.png',
    CT: '/cotton_tail.png',
    SU: '/sunbeam.png',
    MO: '/moonbeam.png',
    EM: '/emerald_gem.png',
    BE: '/bunny_ears.png',
    BG: '/background.png'
  };
  const symbolAliases = ['GF', 'CT', 'SU', 'MO', 'EM', 'BE'];

  // --- Svelte State Variables ---
  let pixiContainer: HTMLDivElement;
  let statusMessage = 'Initializing...';
  let isSpinning = true; // Start as true until game is ready
  let totalWin = 0;

  // --- PixiJS & Game State (non-reactive) ---
  let app: PIXI.Application<PIXI.ICanvas>;
  let symbolTextures: Record<string, PIXI.Texture> = {};
  let spriteGrid: PIXI.Sprite[] = [];
  let mainContainer: PIXI.Container;

  // --- Svelte Lifecycle: onMount ---
  onMount(() => {
    const canvasWidth = GRID_WIDTH * SYMBOL_SIZE + PADDING * 2;
    const canvasHeight = GRID_HEIGHT * SYMBOL_SIZE + PADDING * 2;
    
    const initPixi = async () => {
        try {
            app = new PIXI.Application();
            await app.init({
                width: canvasWidth,
                height: canvasHeight,
                backgroundColor: 0x1a1a2e,
                antialias: true,
            });
            pixiContainer.appendChild(app.view as unknown as Node);

            console.log('Loading assets...');
            await PIXI.Assets.load(Object.values(assetPaths));
            for (const [alias, path] of Object.entries(assetPaths)) {
              symbolTextures[alias] = PIXI.Texture.from(path);
            }
            console.log('Assets loaded.');

            const backgroundSprite = new PIXI.Sprite(symbolTextures['BG']);
            backgroundSprite.width = app.screen.width;
            backgroundSprite.height = app.screen.height;
            app.stage.addChild(backgroundSprite);
            
            mainContainer = new PIXI.Container();
            mainContainer.x = (app.screen.width - GRID_WIDTH * SYMBOL_SIZE) / 2;
            mainContainer.y = (app.screen.height - GRID_HEIGHT * SYMBOL_SIZE) / 2;
            app.stage.addChild(mainContainer);

            createInitialGrid();
            statusMessage = "Ready to Play!";
            isSpinning = false; // Game is now ready to be played
        } catch (error) {
            console.error("Critical error during Pixi initialization:", error);
            statusMessage = "Error: Could not load game assets.";
        }
    };
    
    initPixi();

    return () => {
      if (app) {
        app.destroy(true, { children: true, texture: true, baseTexture: true });
      }
    };
  });

  // --- Grid Management ---
  function createInitialGrid() {
    for (let i = 0; i < GRID_WIDTH * GRID_HEIGHT; i++) {
        const alias = symbolAliases[Math.floor(Math.random() * symbolAliases.length)];
        const sprite = new PIXI.Sprite(symbolTextures[alias]);
        
        sprite.width = SYMBOL_SIZE;
        sprite.height = SYMBOL_SIZE;
        sprite.anchor.set(0.5);
        sprite.x = (i % GRID_WIDTH) * SYMBOL_SIZE + SYMBOL_SIZE / 2;
        
        // Start off-screen for drop-in animation
        const finalY = Math.floor(i / GRID_HEIGHT) * SYMBOL_SIZE + SYMBOL_SIZE / 2;
        sprite.y = -SYMBOL_SIZE;
        
        (sprite as any).symbolAlias = alias;

        mainContainer.addChild(sprite);
        spriteGrid.push(sprite);
        
        gsap.to(sprite, {
            y: finalY,
            duration: 1,
            ease: 'bounce.out',
            delay: (i % GRID_WIDTH) * 0.04 + Math.floor(i / GRID_HEIGHT) * 0.04
        });
    }
  }

  // --- Game Loop ---
  async function handleSpin() {
    if (isSpinning) return;
    
    console.log('--- SPIN INITIATED ---');
    isSpinning = true;
    statusMessage = 'Good Luck!';
    totalWin = 0;

    try {
      console.log('Fetching data from backend...');
      // IMPORTANT: Added Headers and a body to make the POST request more robust.
      const response = await fetch(API_URL, { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ stake: 1 }) // Sending a dummy body
      });

      if (!response.ok) {
        throw new Error(`API response not OK: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Backend response received:', data);
      
      await updateGridState(data.board);
      console.log('Grid visuals updated.');

      if (data.total_win > 0 && data.win_details?.length > 0) {
        console.log('Win detected! Processing sequence...');
        await processWinSequence(data.win_details);
        totalWin = data.total_win;
        statusMessage = `WINNER! You won ${totalWin.toFixed(2)}`;
      } else {
        console.log('No win this round.');
        statusMessage = 'So close! Try again.';
      }

    } catch (error) {
      console.error('Spin Handler Error:', error);
      statusMessage = `Connection Error. Is server running?`;
    } finally {
      console.log('--- SPIN COMPLETE ---');
      isSpinning = false;
    }
  }
  
  // --- Animation & State Update Functions ---
  async function updateGridState(boardData: string[][]) {
      const animations = [];
      for (let row = 0; row < GRID_HEIGHT; row++) {
          for (let col = 0; col < GRID_WIDTH; col++) {
              const spriteIndex = row * GRID_WIDTH + col;
              const backendAlias = boardData[row][col];
              const sprite = spriteGrid[spriteIndex];
              
              if ((sprite as any).symbolAlias !== backendAlias) {
                  (sprite as any).symbolAlias = backendAlias;
                  // Faster, cleaner cross-fade animation
                  const anim = gsap.to(sprite, { 
                    alpha: 0, 
                    duration: 0.15, 
                    onComplete: () => {
                      sprite.texture = symbolTextures[backendAlias];
                      gsap.to(sprite, { alpha: 1, duration: 0.15 });
                    }
                  });
                  animations.push(anim);
              }
          }
      }
      if (animations.length > 0) {
        await Promise.all(animations);
      }
  }

  async function processWinSequence(winDetails: any[]) {
      const winningIndices = new Set<number>();
      winDetails.forEach(cluster => {
          cluster.positions.forEach((pos: [number, number]) => {
              winningIndices.add(pos[0] * GRID_WIDTH + pos[1]);
          });
      });

      const winAnimation = gsap.timeline()
        .to(Array.from(winningIndices).map(i => spriteGrid[i]), {
          pixi: { scale: 1.2, brightness: 1.5 },
          duration: 0.3,
          repeat: 1,
          yoyo: true,
          ease: 'power2.inOut'
        })
        .to(Array.from(winningIndices).map(i => spriteGrid[i]), { 
          alpha: 0, 
          duration: 0.3,
          onComplete: () => {
            winningIndices.forEach(index => {
              spriteGrid[index].renderable = false;
            });
          }
        }, "-=0.2");
      
      await winAnimation;
      await handleCascadeAndFill(winningIndices);
  }

  async function handleCascadeAndFill(removedIndices: Set<number>) {
      const fallAnimations = [];
      for (let col = 0; col < GRID_WIDTH; col++) {
          let emptySlots = 0;
          for (let row = GRID_HEIGHT - 1; row >= 0; row--) {
              const index = row * GRID_WIDTH + col;
              if (removedIndices.has(index)) {
                  emptySlots++;
              } else if (emptySlots > 0) {
                  const sprite = spriteGrid[index];
                  const newRow = row + emptySlots;
                  fallAnimations.push(gsap.to(sprite, {
                      y: newRow * SYMBOL_SIZE + SYMBOL_SIZE / 2,
                      duration: 0.5,
                      ease: 'bounce.out'
                  }));
                  const newIndex = newRow * GRID_WIDTH + col;
                  [spriteGrid[index], spriteGrid[newIndex]] = [spriteGrid[newIndex], spriteGrid[index]];
              }
          }
          
          for(let i = 0; i < emptySlots; i++) {
              const indexToFill = i * GRID_WIDTH + col;
              const sprite = spriteGrid[indexToFill];
              const newAlias = symbolAliases[Math.floor(Math.random() * symbolAliases.length)];
              
              sprite.texture = symbolTextures[newAlias];
              (sprite as any).symbolAlias = newAlias;
              sprite.alpha = 1;
              sprite.renderable = true;
              sprite.y = -SYMBOL_SIZE; // Start above the screen
              
              fallAnimations.push(gsap.to(sprite, {
                  y: i * SYMBOL_SIZE + SYMBOL_SIZE / 2,
                  duration: 0.5,
                  ease: 'bounce.out',
                  delay: i * 0.05
              }));
          }
      }
      if (fallAnimations.length > 0) {
        await Promise.all(fallAnimations);
      }
  }
</script>

<main class="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white p-2">
  <div class="text-center mb-2">
    <h1 class="text-3xl font-bold text-pink-400">BlondeRabbit</h1>
    <p class="text-base text-gray-400 min-h-[24px]">{statusMessage}</p>
  </div>

  <div bind:this={pixiContainer} class="rounded-lg shadow-2xl overflow-hidden border-2 border-pink-500/30 bg-black">
    <!-- PixiJS canvas will be inserted here -->
  </div>

  <div class="mt-4 text-center w-full max-w-sm">
    <div class="mb-3 bg-black/20 p-2 rounded-lg">
        <span class="text-gray-400 uppercase text-xs font-bold">WIN</span>
        <p class="text-4xl font-bold text-yellow-400 tracking-wider tabular-nums">{totalWin.toFixed(2)}</p>
    </div>
    <button
      on:click={handleSpin}
      disabled={isSpinning}
      class="w-full px-8 py-3 text-xl font-bold text-white rounded-full transition-all duration-200
             bg-gradient-to-r from-pink-500 to-purple-600 
             hover:from-pink-600 hover:to-purple-700
             disabled:opacity-50 disabled:cursor-not-allowed
             focus:outline-none focus:ring-4 focus:ring-purple-400/50
             shadow-lg hover:shadow-xl active:scale-95"
    >
      {isSpinning ? '...' : 'SPIN'}
    </button>
  </div>
</main>

<style>
  @tailwind base;
  @tailwind components;
  @tailwind utilities;

  :global(body) {
    font-family: 'Inter', sans-serif;
  }
  
  .tabular-nums {
    font-variant-numeric: tabular-nums;
  }
</style>
