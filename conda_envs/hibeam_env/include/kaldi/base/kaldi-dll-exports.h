
#ifndef kaldi_dll_export_H
#define kaldi_dll_export_H

#if defined(KALDI_DLL_EXPORTS)
#  define KALDI_DLL __declspec(dllexport)
#elif defined(KALDI_DLL_IMPORTS)
#  define KALDI_DLL __declspec(dllimport)
#else
#  define KALDI_DLL
#endif // defined(KALDI_DLL_EXPORTS)

#if defined(KALDI_UTIL_DLL_EXPORTS)
#  define KALDI_UTIL_DLL __declspec(dllexport)
#elif defined(KALDI_UTIL_DLL_IMPORTS)
#  define KALDI_UTIL_DLL __declspec(dllimport)
#else
#  define KALDI_UTIL_DLL
#endif // defined(KALDI_UTIL_DLL_EXPORTS)

#if defined(KALDI_CUMATRIX_DLL_EXPORTS)
#  define KALDI_CUMATRIX_DLL __declspec(dllexport)
#elif defined(KALDI_CUMATRIX_DLL_IMPORTS)
#  define KALDI_CUMATRIX_DLL __declspec(dllimport)
#else
#  define KALDI_CUMATRIX_DLL
#endif // defined(KALDI_CUMATRIX_DLL_EXPORTS)

#endif /* kaldi_dll_export_H */
